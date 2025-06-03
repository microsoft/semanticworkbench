import logging
import time
from typing import Any

import deepmerge
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
)
from openai_client import (
    AzureOpenAIServiceConfig,
    OpenAIRequestConfig,
    OpenAIServiceConfig,
    create_client,
)
from semantic_workbench_api_model.workbench_model import (
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from .models import CompletionResult
from .utils import get_completion

logger = logging.getLogger(__name__)


async def request_completion(
    context: ConversationContext,
    request_config: OpenAIRequestConfig,
    service_config: AzureOpenAIServiceConfig | OpenAIServiceConfig,
    metadata: dict[str, Any],
    metadata_key: str,
    tools: list[ChatCompletionToolParam],
    completion_messages: list[ChatCompletionMessageParam],
) -> CompletionResult:
    """
    Requests a completion from the OpenAI API using the provided configuration and messages.
    This function handles the request, updates metadata with debug information, and returns the completion result.
    """

    # update the metadata with debug information
    deepmerge.always_merger.merge(
        metadata,
        {
            "debug": {
                metadata_key: {
                    "request": {
                        "model": request_config.model,
                        "messages": completion_messages,
                        "max_tokens": request_config.response_tokens,
                        "tools": tools,
                    },
                },
            },
        },
    )

    # Track the start time of the response generation
    response_start_time = time.time()

    # generate a response from the AI model
    completion_status = "reasoning..." if request_config.is_reasoning_model else "thinking..."
    async with create_client(service_config) as client, context.set_status(completion_status):
        try:
            completion = await get_completion(
                client,
                request_config,
                completion_messages,
                tools=tools,
            )

        except Exception as e:
            logger.exception("exception occurred calling openai chat completion")
            completion = None
            deepmerge.always_merger.merge(
                metadata,
                {
                    "debug": {
                        metadata_key: {
                            "error": str(e),
                        },
                    },
                },
            )
            await context.send_messages(
                NewConversationMessage(
                    content="An error occurred while calling the OpenAI API. Is it configured correctly?"
                    " View the debug inspector for more information.",
                    message_type=MessageType.notice,
                    metadata=metadata,
                )
            )

    return CompletionResult(
        response_duration=time.time() - response_start_time,
        completion=completion,
    )
