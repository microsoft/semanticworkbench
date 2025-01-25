import logging
from typing import List

import openai_client
from assistant_extensions.attachments import AttachmentsExtension
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from ..config import AssistantConfigModel
from .utils import (
    build_system_message_content,
    get_history_messages,
)

logger = logging.getLogger(__name__)


async def build_request(
    mcp_prompts: List[str],
    attachments_extension: AttachmentsExtension,
    context: ConversationContext,
    config: AssistantConfigModel,
    silence_token: str,
) -> list[ChatCompletionMessageParam]:
    # Get request configuration for generative model
    generative_request_config = config.generative_ai_client_config.request_config

    # Get the list of conversation participants
    participants_response = await context.get_participants(include_inactive=True)
    participants = participants_response.participants

    # Build system message content
    system_message_content = build_system_message_content(config, context, participants, silence_token)

    # Add MCP Server prompts to the system message content
    if len(mcp_prompts) > 0:
        system_message_content = "\n\n".join([system_message_content, *mcp_prompts])

    completion_messages: List[ChatCompletionMessageParam] = [
        ChatCompletionSystemMessageParam(
            role="system",
            content=system_message_content,
        )
    ]

    # Initialize token count to track the number of tokens used
    token_count = 0

    # Calculate the token count for the messages so far
    token_count += openai_client.num_tokens_from_messages(
        model=generative_request_config.model,
        messages=completion_messages,
    )

    # Generate the attachment messages
    attachment_messages: List[ChatCompletionMessageParam] = openai_client.convert_from_completion_messages(
        await attachments_extension.get_completion_messages_for_attachments(
            context,
            config=config.extensions_config.attachments,
        )
    )

    # Add attachment messages
    completion_messages.extend(attachment_messages)

    token_count += openai_client.num_tokens_from_messages(
        model=generative_request_config.model,
        messages=attachment_messages,
    )

    # Calculate available tokens
    available_tokens = generative_request_config.max_tokens - generative_request_config.response_tokens

    # Get history messages
    history_messages = await get_history_messages(
        context=context,
        participants=participants_response.participants,
        model=generative_request_config.model,
        token_limit=available_tokens - token_count,
    )

    # Add history messages
    completion_messages.extend(history_messages)

    # Check token count
    total_token_count = openai_client.num_tokens_from_messages(
        messages=completion_messages,
        model=generative_request_config.model,
    )
    if total_token_count > available_tokens:
        raise ValueError(
            f"You've exceeded the token limit of {generative_request_config.max_tokens} in this conversation "
            f"({total_token_count}). This assistant does not support recovery from this state. "
            "Please start a new conversation and let us know you ran into this."
        )

    return completion_messages
