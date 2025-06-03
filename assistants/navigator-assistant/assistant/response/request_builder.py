import logging
from dataclasses import dataclass

from openai.types.chat import (
    ChatCompletionDeveloperMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolParam,
)
from openai_client import (
    OpenAIRequestConfig,
    num_tokens_from_tools_and_messages,
)

from .models import ChatMessageProvider

logger = logging.getLogger(__name__)


@dataclass
class BuildRequestResult:
    chat_message_params: list[ChatCompletionMessageParam]
    token_count: int
    token_overage: int


async def build_request(
    request_config: OpenAIRequestConfig,
    tools: list[ChatCompletionToolParam],
    system_message_content: str,
    chat_message_providers: list[ChatMessageProvider],
) -> BuildRequestResult:
    """
    Collect messages for a chat completion request, including system messages and user-provided messages.
    The messages from the chat_message_providers are limited based on the available token budget.
    """

    # Calculate available tokens
    available_tokens = request_config.max_tokens - request_config.response_tokens

    # Add room for reasoning tokens if using a reasoning model
    if request_config.is_reasoning_model:
        available_tokens -= request_config.reasoning_token_allocation

    match request_config.is_reasoning_model:
        case True:
            # Reasoning models use developer messages instead of system messages
            system_message = ChatCompletionDeveloperMessageParam(
                role="developer",
                content=system_message_content,
            )

        case _:
            system_message = ChatCompletionSystemMessageParam(
                role="system",
                content=system_message_content,
            )

    chat_message_params: list[ChatCompletionMessageParam] = [system_message]

    total_token_overage = 0
    for provider in chat_message_providers:
        # calculate the number of tokens that are available for this provider
        available_for_provider = available_tokens - num_tokens_from_tools_and_messages(
            tools=tools,
            messages=chat_message_params,
            model=request_config.model,
        )
        result = await provider(available_for_provider, request_config.model)
        total_token_overage += result.token_overage
        chat_message_params.extend(result.messages)

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

    return BuildRequestResult(
        chat_message_params=chat_message_params,
        token_count=total_token_count,
        token_overage=total_token_overage,
    )
