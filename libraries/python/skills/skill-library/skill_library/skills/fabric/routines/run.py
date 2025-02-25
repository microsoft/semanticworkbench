from pathlib import Path
from typing import Any, cast

from events import MessageEvent
from openai.types.chat import ChatCompletionMessageParam
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


async def main(
    context: RunContext,
    routine_state: dict[str, Any],
    emit: EmitFn,
    run: RunRoutineFn,
    ask_user: AskUserFn,
    pattern: str,
    input: str | None = None,
) -> str:
    """Run a fabric pattern."""

    common_skill = cast(CommonSkill, context.skills["common"])
    language_model = common_skill.config.language_model

    pattern_file = Path(__file__).parent.parent / "patterns" / pattern / "system.md"
    if not pattern_file.exists():
        emit(MessageEvent(message=f"Pattern {pattern} not found."))
        return f"Pattern {pattern} not found."

    with open(pattern_file, "r") as f:
        pattern = f.read()

    messages: list[ChatCompletionMessageParam] = [
        create_system_message(
            pattern,
        )
    ]
    if input:
        messages.append(create_user_message(input))

    completion_args = {
        "model": "gpt-4o",
        "messages": messages,
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
        context.log("gpt_complete", metadata=metadata)
        return message_content_from_completion(completion)
