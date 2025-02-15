import json
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
    options: dict[str, str],
) -> tuple[str, Metadata]:
    """Select the user's intent from a set of options based on the conversation history."""

    common_skill = cast(CommonSkill, context.skills["common"])
    language_model = common_skill.config.language_model

    class Output(BaseModel):
        reasoning: str
        intent: str

    completion_args = {
        "model": "gpt-4o",
        "messages": [
            create_system_message(
                (
                    "A conversation history is a valuable resource for understanding a user's intent. "
                    "By analyzing the context of a conversation, you can identify the user's intent from a set of options. "
                    "Consider the user's previous messages and the overall flow of the conversation to determine the most likely intent."
                    "Select the user's intent from the following options:\n\n"
                    f"{json.dumps(options)}\n\n"
                    "Given a conversation history, reason through what the users intent is and return it the form of a JSON object with reasoning and intent fields."
                )
            ),
            create_user_message(
                f"The conversation: {(await context.conversation_history()).model_dump_json()}",
            ),
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
        intent = cast(Output, completion.choices[0].message.parsed).intent
        return intent, metadata
