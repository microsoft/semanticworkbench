from openai_client import (
    CompletionError,
    create_system_message,
    extra_data,
    make_completion_args_serializable,
    message_content_from_completion,
    validate_completion,
)
from skill_library.types import LanguageModel, Metadata

from ..logging import logger


async def gpt_complete(
    language_model: LanguageModel,
    prompt: str,
) -> tuple[str, Metadata]:
    """Use the vast knowledge of GPT-4 completion using any prompt you provide. All information needed for the prompt should be in the prompt. No other context or content is available from anywhere other than this prompt. Don't refer to content outside the prompt. The prompt can be big. Returns the completion."""

    # Use the language model to generate a response to the user.

    completion_args = {
        "model": "gpt-4o",
        "messages": [
            create_system_message(
                prompt,
            ),
        ],
    }

    metadata = {}
    logger.debug("Completion call.", extra=extra_data(make_completion_args_serializable(completion_args)))
    metadata["completion_args"] = make_completion_args_serializable(completion_args)
    try:
        completion = await language_model.beta.chat.completions.parse(
            **completion_args,
        )
        validate_completion(completion)
        logger.debug("Completion response.", extra=extra_data({"completion": completion.model_dump()}))
        metadata["completion"] = completion.model_dump()
    except Exception as e:
        completion_error = CompletionError(e)
        metadata["completion_error"] = completion_error.message
        logger.error(
            completion_error.message,
            extra=extra_data({"completion_error": completion_error.body, "metadata": metadata}),
        )
        raise completion_error from e
    else:
        return message_content_from_completion(completion), metadata
