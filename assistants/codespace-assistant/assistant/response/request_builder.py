import json
import logging
from dataclasses import dataclass
from typing import List, cast

from assistant_extensions.attachments import AttachmentsConfigModel, AttachmentsExtension
from assistant_extensions.mcp import (
    OpenAISamplingHandler,
    sampling_message_to_chat_completion_message,
)
from assistant_extensions.message_history import message_history_manager_message_provider_for
from mcp.types import SamplingMessage, TextContent
from message_history_manager.history import NewTurn, apply_budget_to_history_messages
from openai.types.chat import (
    ChatCompletionDeveloperMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolParam,
)
from openai_client import (
    OpenAIRequestConfig,
    num_tokens_from_messages,
    num_tokens_from_tools_and_messages,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from ..config import MCPToolsConfigModel, PromptsConfigModel
from ..whiteboard import notify_whiteboard
from .utils import (
    abbreviations,
    build_system_message_content,
)

logger = logging.getLogger(__name__)


@dataclass
class BuildRequestResult:
    chat_message_params: List[ChatCompletionMessageParam]
    token_count: int
    token_overage: int


async def build_request(
    sampling_handler: OpenAISamplingHandler,
    mcp_prompts: List[str],
    attachments_extension: AttachmentsExtension,
    context: ConversationContext,
    prompts_config: PromptsConfigModel,
    request_config: OpenAIRequestConfig,
    tools: List[ChatCompletionToolParam] | None,
    tools_config: MCPToolsConfigModel,
    attachments_config: AttachmentsConfigModel,
    silence_token: str,
    history_turn: NewTurn,
) -> BuildRequestResult:
    # Get the list of conversation participants
    participants_response = await context.get_participants(include_inactive=True)
    participants = participants_response.participants

    additional_system_message_content: list[tuple[str, str]] = []

    # Add any additional tools instructions to the system message content
    if tools_config.enabled:
        additional_system_message_content.append((
            "Tool Instructions",
            tools_config.advanced.additional_instructions,
        ))

    # Add MCP Server prompts to the system message content
    if len(mcp_prompts) > 0:
        additional_system_message_content.append(("Specific Tool Guidance", "\n\n".join(mcp_prompts)))

    # Build system message content
    system_message_content = build_system_message_content(
        prompts_config, context, participants, silence_token, additional_system_message_content
    )

    chat_message_params: List[ChatCompletionMessageParam] = []

    if request_config.is_reasoning_model:
        # Reasoning models use developer messages instead of system messages
        developer_message_content = (
            f"Formatting re-enabled\n{system_message_content}"
            if request_config.enable_markdown_in_reasoning_response
            else system_message_content
        )
        chat_message_params.append(
            ChatCompletionDeveloperMessageParam(
                role="developer",
                content=developer_message_content,
            )
        )
    else:
        chat_message_params.append(
            ChatCompletionSystemMessageParam(
                role="system",
                content=system_message_content,
            )
        )

    # Generate the attachment messages
    # attachment_messages: List[ChatCompletionMessageParam] = convert_from_completion_messages(
    #     await attachments_extension.get_completion_messages_for_attachments(
    #         context,
    #         config=attachments_config,
    #     )
    # )

    # # Add attachment messages
    # chat_message_params.extend(attachment_messages)

    # Initialize token count to track the number of tokens used
    # Add history messages last, as they are what will be truncated if the token limit is reached
    #
    # Here are the parameters that count towards the token limit:
    # - messages
    # - tools
    # - tool_choice
    # - response_format

    # Calculate the token count for everything so far
    consumed_token_count = num_tokens_from_tools_and_messages(
        model=request_config.model,
        messages=chat_message_params,
        tools=tools or [],
    )

    # Calculate the total available tokens for the request (ie. the maximum tokens minus the allocation for the response)
    available_tokens = request_config.max_tokens - request_config.response_tokens

    # Add room for reasoning tokens if using a reasoning model
    if request_config.is_reasoning_model:
        available_tokens -= request_config.reasoning_token_allocation

    message_provider = message_history_manager_message_provider_for(
        context=context, tool_abbreviations=abbreviations.tool_abbreviations
    )

    message_history_token_budget = available_tokens - consumed_token_count

    history_messages = await apply_budget_to_history_messages(
        turn=history_turn,
        token_budget=message_history_token_budget,
        token_counter=lambda messages: num_tokens_from_messages(messages=messages, model=request_config.model),
        message_provider=message_provider,
    )

    # Add history messages
    chat_message_params.extend(history_messages)

    # Check token count
    total_token_count = num_tokens_from_tools_and_messages(
        messages=chat_message_params,
        tools=tools or [],
        model=request_config.model,
    )

    logging.info(
        "chat message params budgeted; message count: %d, total token count: %d",
        len(chat_message_params),
        total_token_count,
    )

    if total_token_count > available_tokens:
        raise ValueError(
            f"You've exceeded the token limit of {request_config.max_tokens} in this conversation "
            f"({total_token_count}). This assistant does not support recovery from this state. "
            "Please start a new conversation and let us know you ran into this."
        )

    # Create a message processor for the sampling handler
    async def message_processor(
        messages: List[SamplingMessage], available_tokens: int, model: str
    ) -> List[ChatCompletionMessageParam]:
        updated_messages: List[ChatCompletionMessageParam] = []

        def add_converted_message(message: SamplingMessage) -> None:
            updated_messages.append(sampling_message_to_chat_completion_message(message))

        for message in messages:
            if not isinstance(message.content, TextContent):
                add_converted_message(message)
                continue

            # Determine if the message.content.text is a json payload
            content = message.content.text
            if not content.startswith("{") or not content.endswith("}"):
                add_converted_message(message)
                continue

            # Attempt to parse the json payload
            try:
                json_payload = json.loads(content)
                variable = json_payload.get("variable")
                match variable:
                    case "attachment_messages":
                        updated_messages.extend([])  # (attachment_messages)
                        continue
                    case "history_messages":
                        updated_messages.extend(history_messages)
                        continue
                    case _:
                        add_converted_message(message)
                        continue

            except json.JSONDecodeError:
                add_converted_message(message)
                continue

        return updated_messages

    # Notify the whiteboard of the latest context (messages)
    await notify_whiteboard(
        context=context,
        server_config=tools_config.hosted_mcp_servers.memory_whiteboard,
        attachment_messages=[],  # attachment_messages,
        chat_messages=cast(list[ChatCompletionMessageParam], history_messages),
    )

    # Set the message processor for the sampling handler
    sampling_handler.message_processor = message_processor

    return BuildRequestResult(
        chat_message_params=chat_message_params,
        token_count=total_token_count,
        token_overage=0,
    )
