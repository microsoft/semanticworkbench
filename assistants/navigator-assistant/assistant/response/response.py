import logging
from contextlib import AsyncExitStack
from textwrap import dedent
from typing import Any, Callable

from assistant_extensions.attachments import AttachmentsExtension
from assistant_extensions.mcp import (
    MCPClientSettings,
    MCPServerConnectionError,
    OpenAISamplingHandler,
    establish_mcp_sessions,
    get_enabled_mcp_server_configs,
    get_mcp_server_prompts,
    list_roots_callback_for,
    refresh_mcp_sessions,
)
from mcp import ServerNotification
from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    ConversationParticipant,
    MessageType,
    NewConversationMessage,
    UpdateParticipant,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from ..config import AssistantConfigModel
from .local_tool import add_assistant_to_conversation_tool
from .local_tool.list_assistant_services import get_assistant_services
from .step_handler import next_step
from .utils import get_ai_client_configs

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

    async with AsyncExitStack() as stack:
        # Get the AI client configurations for this assistant
        generative_ai_client_config = get_ai_client_configs(config, "generative")
        reasoning_ai_client_config = get_ai_client_configs(config, "reasoning")

        # TODO: This is a temporary hack to allow directing the request to the reasoning model
        # Currently we will only use the requested AI client configuration for the turn
        request_type = "reasoning" if message.content.startswith("reason:") else "generative"
        # Set a default AI client configuration based on the request type
        default_ai_client_config = (
            reasoning_ai_client_config if request_type == "reasoning" else generative_ai_client_config
        )
        # Set the service and request configurations for the AI client
        service_config = default_ai_client_config.service_config
        request_config = default_ai_client_config.request_config

        # Create a sampling handler for handling requests from the MCP servers
        sampling_handler = OpenAISamplingHandler(
            ai_client_configs=[
                generative_ai_client_config,
                reasoning_ai_client_config,
            ]
        )

        async def message_handler(message) -> None:
            if isinstance(message, ServerNotification) and message.root.method == "notifications/message":
                await context.update_participant_me(UpdateParticipant(status=f"{message.root.params.data}"))

        enabled_servers = []
        if config.tools.enabled:
            enabled_servers = get_enabled_mcp_server_configs(config.tools.mcp_servers)

        try:
            mcp_sessions = await establish_mcp_sessions(
                client_settings=[
                    MCPClientSettings(
                        server_config=server_config,
                        sampling_callback=sampling_handler.handle_message,
                        message_handler=message_handler,
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

        # Retrieve prompts from the MCP servers
        mcp_prompts = await get_mcp_server_prompts(mcp_sessions)

        # Initialize a loop control variable
        max_steps = config.tools.advanced.max_steps
        interrupted = False
        encountered_error = False
        completed_within_max_steps = False
        step_count = 0

        participants_response = await context.get_participants()
        assistant_list = await get_assistant_services(context)

        # Loop until the response is complete or the maximum number of steps is reached
        while step_count < max_steps:
            step_count += 1

            # Check to see if we should interrupt our flow
            last_message = await context.get_messages(limit=1, message_types=[MessageType.chat, MessageType.command])

            if (
                step_count > 1
                and last_message.messages[0].sender.participant_id != context.assistant.id
                and last_message.messages[0].id != message.id
            ):
                # The last message was from a sender other than the assistant, so we should
                # interrupt our flow as this would have kicked off a new response from this
                # assistant with the new message in mind and that process can decide if it
                # should continue with the current flow or not.
                interrupted = True
                logger.info("Response interrupted.")
                await context.send_messages(
                    NewConversationMessage(
                        content="Response interrupted due to new message.",
                        message_type=MessageType.notice,
                        metadata=metadata,
                    )
                )
                break

            # Reconnect to the MCP servers if they were disconnected
            mcp_sessions = await refresh_mcp_sessions(mcp_sessions)

            step_result = await next_step(
                sampling_handler=sampling_handler,
                mcp_sessions=mcp_sessions,
                attachments_extension=attachments_extension,
                context=context,
                request_config=request_config,
                service_config=service_config,
                tools_config=config.tools,
                attachments_config=config.extensions_config.attachments,
                metadata=metadata,
                metadata_key=f"respond_to_conversation:step_{step_count}",
                local_tools=[add_assistant_to_conversation_tool],
                system_message_content=combined_prompt(
                    config.prompts.instruction_prompt,
                    'Your name is "{context.assistant.name}".',
                    conditional_prompt(
                        len(participants_response.participants) > 2 and not message.mentions(context.assistant.id),
                        lambda: participants_system_prompt(
                            context, participants_response.participants, silence_token="{{SILENCE}}"
                        ),
                    ),
                    "# Workflow Guidance:",
                    config.prompts.guidance_prompt,
                    "# Safety Guardrails:",
                    config.prompts.guardrails_prompt,
                    conditional_prompt(
                        config.tools.enabled,
                        lambda: combined_prompt(
                            "# Tool Instructions",
                            config.tools.advanced.additional_instructions,
                        ),
                    ),
                    conditional_prompt(
                        len(mcp_prompts) > 0,
                        lambda: combined_prompt("# Specific Tool Guidance", "\n\n".join(mcp_prompts)),
                    ),
                    "# Semantic Workbench Guide:",
                    config.prompts.semantic_workbench_guide_prompt,
                    "# Assistant Service List",
                    assistant_list,
                ),
            )

            if step_result.status == "error":
                encountered_error = True
                break

            if step_result.status == "final":
                completed_within_max_steps = True
                break

        # If the response did not complete within the maximum number of steps, send a message to the user
        if not completed_within_max_steps and not encountered_error and not interrupted:
            await context.send_messages(
                NewConversationMessage(
                    content=config.tools.advanced.max_steps_truncation_message,
                    message_type=MessageType.notice,
                    metadata=metadata,
                )
            )
            logger.info("Response stopped early due to maximum steps.")

        # Log the completion of the response
        logger.info(
            "Response completed; interrupted: %s, completed_within_max_steps: %s, encountered_error: %s, step_count: %d",
            interrupted,
            completed_within_max_steps,
            encountered_error,
            step_count,
        )


def conditional_prompt(condition: bool, content: Callable[[], str]) -> str:
    """
    Generate a system message prompt based on a condition.
    """

    if condition:
        return content()

    return ""


def participants_system_prompt(
    context: ConversationContext, participants: list[ConversationParticipant], silence_token: str
) -> str:
    """
    Generate a system message prompt based on the participants in the conversation.
    """

    participant_names = ", ".join([
        f'"{participant.name}"' for participant in participants if participant.id != context.assistant.id
    ])
    system_message_content = dedent(f"""
        There are {len(participants)} participants in the conversation,
        including you as the assistant, with the name {context.assistant.name}, and the following users: {participant_names}.
        \n\n
        You do not need to respond to every message. Do not respond if the last thing said was a closing
        statement such as "bye" or "goodbye", or just a general acknowledgement like "ok" or "thanks". Do not
        respond as another user in the conversation, only as "{context.assistant.name}".
        \n\n
        Say "{silence_token}" to skip your turn.
    """).strip()

    return system_message_content


def combined_prompt(*parts: str) -> str:
    return "\n\n".join((part for part in parts if part)).strip()
