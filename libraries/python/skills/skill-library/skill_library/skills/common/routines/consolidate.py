from typing import Any, Optional, cast

from openai_client import (
    CompletionError,
    create_system_message,
    create_user_message,
    extra_data,
    make_completion_args_serializable,
    message_content_from_completion,
    validate_completion,
)
from skill_library import AskUserFn, EmitFn, RunContext, RunRoutineFn
from skill_library.logging import logger
from skill_library.skills.common import CommonSkill

DEFAULT_MAX_LENGTH = 10000


async def main(
    context: RunContext,
    routine_state: dict[str, Any],
    emit: EmitFn,
    run: RunRoutineFn,
    ask_user: AskUserFn,
    content: str,
    max_length: Optional[int] = DEFAULT_MAX_LENGTH,
) -> str:
    """
    Consolidate various pieces of content into a cohesive whole.
    """
    common_skill = cast(CommonSkill, context.skills["common"])
    language_model = common_skill.config.language_model

    system_message = "Consolide the content provided by the user into a cohesive whole. Try not to lose any information, but reorder and deduplicate as necessary and give it all a singular tone. Just respond with your consolidated content."

    completion_args = {
        "model": "gpt-4o",
        "messages": [
            create_system_message(system_message),
            create_user_message(content),
        ],
        "max_tokens": max_length,
    }

    logger.debug("Completion call.", extra=extra_data(make_completion_args_serializable(completion_args)))
    metadata = {}
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
            extra=extra_data({"completion_error": completion_error.body, "metadata": context.metadata_log}),
        )
        raise completion_error from e
    else:
        consolidation = message_content_from_completion(completion)
        metadata["consolidation"] = consolidation
        return consolidation
    finally:
        context.log("consolidated", metadata)
