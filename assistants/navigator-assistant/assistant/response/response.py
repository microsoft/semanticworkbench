import logging
from contextlib import AsyncExitStack
from typing import Any, Literal
from uuid import UUID

from assistant_extensions.attachments import AttachmentsConfigModel, AttachmentsExtension
from assistant_extensions.mcp import (
    MCPClientSettings,
    MCPServerConnectionError,
    OpenAISamplingHandler,
    SamplingChatMessageProvider,
    establish_mcp_sessions,
    get_enabled_mcp_server_configs,
    list_roots_callback_for,
    refresh_mcp_sessions,
)
from mcp import ServerNotification
from mcp.client.session import MessageHandlerFnT
from openai.types.chat import ChatCompletionMessageParam
from openai_client import (
    AzureOpenAIServiceConfig,
    OpenAIRequestConfig,
    OpenAIServiceConfig,
    convert_from_completion_messages,
)
from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    ConversationParticipant,
    MessageType,
    NewConversationMessage,
    ParticipantRole,
    UpdateParticipant,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from ..config import AssistantConfigModel
from ..whiteboard import get_whiteboard_service_config, notify_whiteboard
from . import prompt
from .local_tool import add_assistant_to_conversation_tool
from .models import ChatMessageProvider, TokenConstrainedChatMessageList
from .step_handler import next_step
from .utils import get_ai_client_configs, get_tools_from_mcp_sessions
from .utils.message_utils import get_history_messages

logger = logging.getLogger(__name__)


async def respond_to_conversation(
    message: ConversationMessage,
    attachments_extension: AttachmentsExtension,
    context: ConversationContext,
    config: AssistantConfigModel,
    metadata: dict[str, Any] = {},
) -> None:
    """
    Perform a multi-step response to a conversation message using dynamically loaded MCP servers with
    support for multiple tool invocations.
    """

    # TODO: This is a temporary hack to allow directing the request to the reasoning model
    # Currently we will only use the requested AI client configuration for the turn
    request_type = "reasoning" if message.content.startswith("reason:") else "generative"

    service_config, request_config = get_ai_configs_for_response(config, request_type)

    get_attachment_chat_messages = context_bound_get_attachment_messages_source(
        context, attachments_extension, config.extensions_config.attachments
    )
    get_history_chat_messages = context_bound_get_history_chat_messages_source(
        context, (await context.get_participants()).participants
    )

    # Notify the whiteboard of the latest context (messages)
    await notify_whiteboard(
        context=context,
        server_config=get_whiteboard_service_config(config),
        attachment_message_provider=get_attachment_chat_messages,
        chat_message_provider=get_history_chat_messages,
    )

    # Create a sampling handler for handling requests from the MCP servers
    sampling_handler = OpenAISamplingHandler(
        ai_client_configs=[
            get_ai_client_configs(config, "generative"),
            get_ai_client_configs(config, "reasoning"),
        ],
        message_providers={
            "attachment_messages": to_sampling_message_provider(get_attachment_chat_messages),
            "history_messages": to_sampling_message_provider(get_history_chat_messages),
        },
    )

    enabled_servers = []
    if config.tools.enabled:
        enabled_servers = get_enabled_mcp_server_configs(config.tools.mcp_servers)

    async with AsyncExitStack() as stack:
        try:
            mcp_sessions = await establish_mcp_sessions(
                client_settings=[
                    MCPClientSettings(
                        server_config=server_config,
                        sampling_callback=sampling_handler.handle_message,
                        message_handler=context_bound_mcp_client_message_handler(context),
                        list_roots_callback=list_roots_callback_for(context=context, server_config=server_config),
                    )
                    for server_config in enabled_servers
                ],
                stack=stack,
            )

        except MCPServerConnectionError as e:
            await context.send_messages(
                NewConversationMessage(
                    content=f"Failed to connect to MCP server {e.server_config.key}: {e}",
                    message_type=MessageType.notice,
                    metadata=metadata,
                )
            )
            return

        system_message_content = await prompt.build_system_message(
            context, config, request_config, message, mcp_sessions
        )

        executable_tools = [
            add_assistant_to_conversation_tool.to_executable(),
            *get_tools_from_mcp_sessions(mcp_sessions, config.tools),
        ]

        response_status: Literal["completed", "error", "interrupted", "exceeded_max_steps"] = "exceeded_max_steps"
        step_count = 0

        # Loop until the response is complete or the maximum number of steps is reached
        while step_count < config.tools.advanced.max_steps:
            step_count += 1

            if await new_user_message_exists(context=context, after_message_id=message.id):
                # A new message has been sent by a user, so we should
                # interrupt our flow as this would have kicked off a new response from this
                # assistant with the new message in mind and that process can decide if it
                # should continue with the current flow or not.
                response_status = "interrupted"
                break

            # Reconnect to the MCP servers if they were disconnected
            mcp_sessions = await refresh_mcp_sessions(mcp_sessions, stack)

            metadata_key = f"respond_to_conversation:step_{step_count}"

            step_result = await next_step(
                context=context,
                service_config=service_config,
                request_config=request_config,
                executable_tools=executable_tools,
                system_message_content=system_message_content,
                chat_message_providers=[
                    get_attachment_chat_messages,
                    get_history_chat_messages,
                ],
                metadata=metadata,
                metadata_key=metadata_key,
            )

            match step_result.status:
                case "final":
                    response_status = "completed"
                    break

                case "error":
                    response_status = "error"
                    break

                case "continue":
                    pass

                case _:
                    raise ValueError(f"Unexpected step result status: {step_result.status}.")

        # Notify for incomplete (not complete or error) response statuses
        match response_status:
            case "interrupted":
                await context.send_messages(
                    NewConversationMessage(
                        content="Response interrupted due to new message.",
                        message_type=MessageType.notice,
                        metadata=metadata,
                    )
                )

            case "exceeded_max_steps":
                # If the response did not complete within the maximum number of steps, send a message to the user
                await context.send_messages(
                    NewConversationMessage(
                        content=config.tools.advanced.max_steps_truncation_message,
                        message_type=MessageType.notice,
                        metadata=metadata,
                    )
                )

        # Log the completion of the response
        logger.info("Response finished; status: %s, step_count: %d", response_status, step_count)


def get_ai_configs_for_response(
    config: AssistantConfigModel, request_type: Literal["generative", "reasoning"]
) -> tuple[AzureOpenAIServiceConfig | OpenAIServiceConfig, OpenAIRequestConfig]:
    """
    Get the AI client configurations for the response based on the request type.
    """
    # Get the AI client configurations for this assistant
    generative_ai_client_config = get_ai_client_configs(config, "generative")
    reasoning_ai_client_config = get_ai_client_configs(config, "reasoning")

    # Set a default AI client configuration based on the request type
    default_ai_client_config = (
        reasoning_ai_client_config if request_type == "reasoning" else generative_ai_client_config
    )
    # Set the service and request configurations for the AI client
    return default_ai_client_config.service_config, default_ai_client_config.request_config


async def new_user_message_exists(context: ConversationContext, after_message_id: UUID) -> bool:
    """Returns True if there are new user messages after the given message ID."""
    new_user_messages = await context.get_messages(
        limit=1,
        after=after_message_id,
        participant_role=ParticipantRole.user,
    )

    return len(new_user_messages.messages) > 0


def context_bound_mcp_client_message_handler(context: ConversationContext) -> MessageHandlerFnT:
    """
    Returns an MCP message handler function that updates the participant's status based on server notifications.
    """

    async def func(message):
        if isinstance(message, ServerNotification) and message.root.method == "notifications/message":
            await context.update_participant_me(UpdateParticipant(status=f"{message.root.params.data}"))

    return func


def context_bound_get_attachment_messages_source(
    context: ConversationContext,
    attachments_extension: AttachmentsExtension,
    config: AttachmentsConfigModel,
) -> ChatMessageProvider:
    """
    Returns a chat message provider that retrieves attachment messages for the conversation context.
    """

    async def func(
        available_tokens: int,
        model: str,
    ) -> TokenConstrainedChatMessageList:
        return TokenConstrainedChatMessageList(
            messages=convert_from_completion_messages(
                await attachments_extension.get_completion_messages_for_attachments(
                    context,
                    config=config,
                )
            ),
            token_overage=0,
        )

    return func


def context_bound_get_history_chat_messages_source(
    context: ConversationContext,
    participants: list[ConversationParticipant],
) -> ChatMessageProvider:
    """
    Returns a chat message provider that retrieves history messages for the conversation context.
    """

    async def func(available_tokens: int, model: str) -> TokenConstrainedChatMessageList:
        history_messages_result = await get_history_messages(
            context=context,
            participants=participants,
            model=model,
            token_limit=available_tokens,
        )
        return TokenConstrainedChatMessageList(
            messages=history_messages_result.messages, token_overage=history_messages_result.token_overage
        )

    return func


def to_sampling_message_provider(provider: ChatMessageProvider) -> SamplingChatMessageProvider:
    """
    Converts a ChatMessageProvider to a SamplingChatMessageProvider.
    This is used to adapt the provider for use with the OpenAISamplingHandler.
    """

    async def wrapped(available_tokens: int, model: str) -> list[ChatCompletionMessageParam]:
        result = await provider(available_tokens, model)
        return result.messages

    return wrapped
