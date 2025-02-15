from typing import Any, cast

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

SYSTEM_PROMPT = """
You are a part of an AGI system that generates routines to satisfy a specific goal. Routines are the building blocks of the AGI system and can be thought of as procedural knowledge. Routines can execute other routines, ask the user for input, and emit messages to the user. Routines can be used to perform a wide variety of tasks, such as generating text, answering questions, or performing calculations.

Routine functions are put in a module and shipped as part of "skill" packages. Skills are Python packages that contain a set of routines. An AGI system can have multiple skills, each with its own set of routines. Skills are loaded into the AGI system at runtime and can be used to extend the capabilities of the system. Each skill has its own configuration, which is used to initialize the skill and its routines.

Routine specification:

A routine is a Python function that takes a RunContext, routine_state, emit, run, and ask_user as arguments. The function can return anything. Here's what the required arguments can be used for:

- context: The context of the conversation. You can use this to get information about the user's goal and the current state of the conversation. The context has the following attributes:
  - session_id: A unique identifier for the session. This is useful for tracking the conversation.
  - run_id: A unique identifier for the run. This is useful for tracking the conversation.
  - run_drive: A drive object that can be used to read and write files to a particular location. This is useful for storing data that needs to persist between sessions.
  - skills: A dictionary of skills that are available to the routine. Each skill has a name and a function that can be used to run the skill.
  - log(Metadata): A function that can be used to log metadata about the conversation. This is our primary logging mechanism. Metadata is a dictionary of key-value pairs (dict[str, Any]).
- routine_state: A dictionary that can be used to store state between steps in the routine. This is useful for maintaining context between messages.
- emit: A function that can be used to emit messages to the user. This is useful for asking the user for input or providing updates on the progress of the routine.
- run: A function that can be used to run other routines. This is useful for breaking up a large routine into smaller, more manageable pieces. A list of all available routines is below.
- ask_user: A function that can be used to ask the user for input. This is useful for getting information from the user that is needed to complete the routine.

Available routines:

{{routines}}

Your job is to respond to a user's description of their goal by returning a routine that satisfies the goal. Respond with just the routine.

Example:

async def main(
    context: RunContext,
    routine_state: dict[str, Any],
    emit: EmitFn,
    run: RunRoutineFn,
    ask_user: AskUserFn,
    another_arg: str,
) -> str:

    # Skills can be configured with arbitrary arguments. These can be used in the routine by referencing any skill instance from the context.
    common_skill = cast(CommonSkill, context.skills["common"])
    language_model = common_skill.language_model

    ask_user("What is your name?")
    run("common.", another_arg)
"""


async def main(
    context: RunContext,
    routine_state: dict[str, Any],
    emit: EmitFn,
    run: RunRoutineFn,
    ask_user: AskUserFn,
    goal: str,
) -> str:
    """Generate a routine to satisfy a specific goal."""

    common_skill = cast(CommonSkill, context.skills["common"])
    language_model = common_skill.config.language_model

    completion_args = {
        "model": "gpt-4o",
        "messages": [
            create_system_message(SYSTEM_PROMPT),
            create_user_message(
                goal,
            ),
        ],
    }

    logger.debug("Completion call.", extra=extra_data(make_completion_args_serializable(completion_args)))
    context.log({"completion_args": make_completion_args_serializable(completion_args)})
    try:
        completion = await language_model.beta.chat.completions.parse(
            **completion_args,
        )
        validate_completion(completion)
        logger.debug("Completion response.", extra=extra_data({"completion": completion.model_dump()}))
        context.log({"completion": completion.model_dump()})
    except Exception as e:
        completion_error = CompletionError(e)
        context.log({"completion_error": completion_error.message})
        logger.error(
            completion_error.message,
            extra=extra_data({"completion_error": completion_error.body, "metadata": context.metadata_log}),
        )
        raise completion_error from e
    else:
        search_query = message_content_from_completion(completion).strip().strip('"')
        context.log({"search_query": search_query})
        return search_query
