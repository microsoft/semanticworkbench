from importlib.resources import files
from typing import Any, cast

from openai_client import (
    CompletionError,
    create_system_message,
    create_user_message,
    extra_data,
    format_with_liquid,
    make_completion_args_serializable,
    message_content_from_completion,
    validate_completion,
)
from skill_library import AskUserFn, EmitFn, RunContext, RunRoutineFn
from skill_library.logging import logger
from skill_library.skills.common import CommonSkill

SYSTEM_PROMPT = """
<CONTEXT>

{{llm_info}}

### Available skills and thier configuration

{{skills}}


### Available routines

{{routines}}

</CONTEXT>

<INSTRUCTIONS>

You are a part of an AGI system that generates routines to satisfy a specific goal. Routines are the building blocks of the AGI system and can be thought of as procedural knowledge.

Your job is to respond to a user's description of their goal by returning a routine that satisfies the goal. Respond with the code for a routine that is consistent with the API described above, delimited by markdown python triple backticks.

</INSTRUCTIONS>
"""


async def main(
    context: RunContext,
    routine_state: dict[str, Any],
    emit: EmitFn,
    run: RunRoutineFn,
    ask_user: AskUserFn,
    goal: str,
) -> str:
    """Generate a skill library routine to satisfy a specific goal."""

    common_skill = cast(CommonSkill, context.skills["common"])
    language_model = common_skill.config.language_model
    llm_info = files("skill_library").joinpath("llm_info.txt").read_text()

    skill_configs = []
    for skill in context.skills.values():
        skill_configs.append(skill.config.model_dump())

    system_prompt = format_with_liquid(
        SYSTEM_PROMPT, {"llm_info": llm_info, "routines": context.routine_usage(), "skills": skill_configs}
    )
    completion_args = {
        "model": "gpt-4o",
        "messages": [
            create_system_message(system_prompt),
            create_user_message(
                goal,
            ),
        ],
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
        routine = message_content_from_completion(completion).strip()
        metadata["routine"] = routine
        # emit(MessageEvent(message=routine))
        return routine
    finally:
        context.log("generate_routine", metadata)
