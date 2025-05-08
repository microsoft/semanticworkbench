import json
import logging
from dataclasses import dataclass
from typing import List

from assistant_extensions.attachments import AttachmentsConfigModel, AttachmentsExtension
from assistant_extensions.mcp import (
    OpenAISamplingHandler,
    sampling_message_to_chat_completion_message,
)
from mcp.types import SamplingMessage, TextContent
from openai.types.chat import (
    ChatCompletionDeveloperMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolParam,
)
from openai_client import (
    OpenAIRequestConfig,
    convert_from_completion_messages,
    num_tokens_from_messages,
    num_tokens_from_tools,
    num_tokens_from_tools_and_messages,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from ..config import MCPToolsConfigModel
from ..whiteboard import notify_whiteboard
from .utils import get_history_messages

logger = logging.getLogger(__name__)


@dataclass
class BuildRequestResult:
    chat_message_params: List[ChatCompletionMessageParam]
    token_count: int
    token_overage: int


async def build_request(
    sampling_handler: OpenAISamplingHandler,
    attachments_extension: AttachmentsExtension,
    context: ConversationContext,
    request_config: OpenAIRequestConfig,
    tools: List[ChatCompletionToolParam],
    tools_config: MCPToolsConfigModel,
    attachments_config: AttachmentsConfigModel,
    system_message_content: str,
) -> BuildRequestResult:
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

    # Initialize token count to track the number of tokens used
    # Add history messages last, as they are what will be truncated if the token limit is reached
    #
    # Here are the parameters that count towards the token limit:
    # - messages
    # - tools
    # - tool_choice
    # - response_format
    # - seed (if set, minor impact)

    # Get the token count for the tools
    tool_token_count = num_tokens_from_tools(
        model=request_config.model,
        tools=tools,
    )

    # Generate the attachment messages
    attachment_messages: List[ChatCompletionMessageParam] = convert_from_completion_messages(
        await attachments_extension.get_completion_messages_for_attachments(
            context,
            config=attachments_config,
        )
    )

    # Add attachment messages
    chat_message_params.extend(attachment_messages)

    token_count = num_tokens_from_messages(
        model=request_config.model,
        messages=chat_message_params,
    )

    # Calculate available tokens
    available_tokens = request_config.max_tokens - request_config.response_tokens

    # Add room for reasoning tokens if using a reasoning model
    if request_config.is_reasoning_model:
        available_tokens -= request_config.reasoning_token_allocation

    # Get history messages
    participants_response = await context.get_participants()
    history_messages_result = await get_history_messages(
        context=context,
        participants=participants_response.participants,
        model=request_config.model,
        token_limit=available_tokens - token_count - tool_token_count,
    )

    # Add history messages
    chat_message_params.extend(history_messages_result.messages)

    # Check token count
    total_token_count = num_tokens_from_tools_and_messages(
        messages=chat_message_params,
        tools=tools,
        model=request_config.model,
    )
    if total_token_count > available_tokens:
        raise ValueError(
            f"You've exceeded the token limit of {request_config.max_tokens} in this conversation "
            f"({total_token_count}). This assistant does not support recovery from this state. "
            "Please start a new conversation and let us know you ran into this."
        )

    # Create a message processor for the sampling handler
    def message_processor(messages: List[SamplingMessage]) -> List[ChatCompletionMessageParam]:
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
                        updated_messages.extend(attachment_messages)
                        continue
                    case "history_messages":
                        updated_messages.extend(history_messages_result.messages)
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
        attachment_messages=attachment_messages,
        chat_messages=history_messages_result.messages,
    )

    # Set the message processor for the sampling handler
    sampling_handler.message_processor = message_processor

    return BuildRequestResult(
        chat_message_params=chat_message_params,
        token_count=total_token_count,
        token_overage=history_messages_result.token_overage,
    )
