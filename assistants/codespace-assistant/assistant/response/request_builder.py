import logging
from dataclasses import dataclass
from typing import List

from assistant_extensions.attachments import AttachmentsConfigModel, AttachmentsExtension
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

from assistant.config import PromptsConfigModel
from assistant.extensions.tools.__model import ToolsConfigModel

from .utils import (
    build_system_message_content,
    get_history_messages,
)

logger = logging.getLogger(__name__)


@dataclass
class BuildRequestResult:
    chat_message_params: List[ChatCompletionMessageParam]
    token_count: int
    token_overage: int


async def build_request(
    mcp_prompts: List[str],
    attachments_extension: AttachmentsExtension,
    context: ConversationContext,
    prompts_config: PromptsConfigModel,
    request_config: OpenAIRequestConfig,
    tools: List[ChatCompletionToolParam] | None,
    tools_config: ToolsConfigModel,
    attachments_config: AttachmentsConfigModel,
    silence_token: str,
) -> BuildRequestResult:
    # Get the list of conversation participants
    participants_response = await context.get_participants(include_inactive=True)
    participants = participants_response.participants

    additional_system_message_content: list[tuple[str, str]] = []

    # Add any additional tools instructions to the system message content
    if tools_config.enabled:
        additional_system_message_content.append((
            "Tool Instructions",
            tools_config.additional_instructions,
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
        ChatCompletionSystemMessageParam(
            role="system",
            content=system_message_content,
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

    # Calculate the token count for the messages so far
    token_count = num_tokens_from_messages(
        model=request_config.model,
        messages=chat_message_params,
    )

    # Get the token count for the tools
    tool_token_count = num_tokens_from_tools(
        model=request_config.model,
        tools=tools or [],
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

    token_count += num_tokens_from_messages(
        model=request_config.model,
        messages=attachment_messages,
    )

    # Calculate available tokens
    available_tokens = request_config.max_tokens - request_config.response_tokens

    # Add room for reasoning tokens if using a reasoning model
    if request_config.is_reasoning_model:
        available_tokens -= request_config.reasoning_token_allocation

    # Get history messages
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
        tools=tools or [],
        model=request_config.model,
    )
    if total_token_count > available_tokens:
        raise ValueError(
            f"You've exceeded the token limit of {request_config.max_tokens} in this conversation "
            f"({total_token_count}). This assistant does not support recovery from this state. "
            "Please start a new conversation and let us know you ran into this."
        )

    return BuildRequestResult(
        chat_message_params=chat_message_params,
        token_count=total_token_count,
        token_overage=history_messages_result.token_overage,
    )
