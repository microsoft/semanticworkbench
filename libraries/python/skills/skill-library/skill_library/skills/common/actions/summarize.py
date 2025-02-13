from typing import Optional, cast

from openai_client import (
    CompletionError,
    create_system_message,
    create_user_message,
    extra_data,
    make_completion_args_serializable,
    message_content_from_completion,
    validate_completion,
)
from skill_library import RunContext
from skill_library.logging import logger
from skill_library.skills.common import CommonSkill
from skill_library.types import Metadata

DEFAULT_MAX_SUMMARY_LENGTH = 5000


async def summarize(
    context: RunContext,
    content: str,
    aspect: Optional[str] = None,
    max_length: Optional[int] = DEFAULT_MAX_SUMMARY_LENGTH,
) -> tuple[str, Metadata]:
    """
    Summarize the content from the given aspect. The content may be relevant or
    not to a given aspect. If no aspect is provided, summarize the content as
    is.
    """
    common_skill = cast(CommonSkill, context.skills["common"])
    language_model = common_skill.config.language_model

    system_message = "You are a summarizer. Your job is to summarize the content provided by the user."
    if aspect:
        system_message += f" Summarize the content only from this aspect: {aspect}"

    completion_args = {
        "model": "gpt-4o",
        "messages": [
            create_system_message(system_message),
            create_user_message(content),
        ],
        "max_tokens": max_length,
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


__default__ = summarize
