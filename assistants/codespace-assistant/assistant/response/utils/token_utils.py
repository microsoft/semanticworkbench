import logging
from typing import Any, Sequence

import deepmerge
from assistant_extensions.ai_clients.model import CompletionMessage
from semantic_workbench_api_model.workbench_model import (
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from ..providers import NumberTokensResult, ResponseProvider

logger = logging.getLogger(__name__)


async def num_tokens_from_messages(
    context: ConversationContext,
    response_provider: ResponseProvider,
    messages: Sequence[CompletionMessage],
    model: str,
    metadata: dict[str, Any],
    metadata_key: str,
) -> NumberTokensResult | None:
    """
    Calculate the number of tokens required to generate the completion messages.
    """
    try:
        return await response_provider.num_tokens_from_messages(
            messages=messages, model=model, metadata_key=metadata_key
        )
    except Exception as e:
        logger.exception(f"exception occurred calculating token count: {e}")
        deepmerge.always_merger.merge(
            metadata,
            {
                "debug": {
                    metadata_key: {
                        "num_tokens_from_messages": {
                            "request": {
                                "messages": messages,
                                "model": model,
                            },
                            "error": str(e),
                        },
                    },
                }
            },
        )
        await context.send_messages(
            NewConversationMessage(
                content="An error occurred while calculating the token count for the messages.",
                message_type=MessageType.notice,
                metadata=metadata,
            )
        )
