from typing import Any, cast

from openai_client import (
    CompletionError,
    create_system_message,
    create_user_message,
    extra_data,
    make_completion_args_serializable,
    validate_completion,
)
from pydantic import BaseModel
from skill_library import AskUserFn, EmitFn, Metadata, RunContext, RunRoutineFn
from skill_library.logging import logger
from skill_library.skills.common import CommonSkill


async def main(
    context: RunContext,
    routine_state: dict[str, Any],
    emit: EmitFn,
    run: RunRoutineFn,
    ask_user: AskUserFn,
    question: str,
    answer: str,
) -> tuple[bool, Metadata]:
    """Decide whether an answer actually answers a question well, and return a reason why."""

    common_skill = cast(CommonSkill, context.skills["common"])
    language_model = common_skill.config.language_model

    class Output(BaseModel):
        reasoning: str
        is_good_answer: bool

    completion_args = {
        "model": "gpt-4o",
        "messages": [
            create_system_message(
                (
                    "Given a question and and an answer, reason through whether or not the answer actually answers the question. Return your reasoning and whether or not the answer is a good answer as JSON."
                )
            ),
            create_user_message((f"The question: {question}\n\bThe answer: {answer}\n\n")),
        ],
        "response_format": Output,
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
        response: Output = cast(Output, completion.choices[0].message.parsed)
        return response.is_good_answer, metadata
