from typing import Any, cast

from events import MessageEvent
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

SYSTEM_PROMPT = '''
You are a part of an AGI system that generates routines to satisfy a specific goal. Routines are the building blocks of the AGI system and can be thought of as procedural knowledge. Routines can execute other routines, ask the user for input, and emit messages to the user. Routines can be used to perform a wide variety of tasks, such as generating text, answering questions, or performing calculations.

Routine functions are put in a module and shipped as part of "skill" packages. Skills are Python packages that contain a set of routines. An AGI system can have multiple skills, each with its own set of routines. Skills are loaded into the AGI system at runtime and can be used to extend the capabilities of the system. Each skill has its own configuration, which is used to initialize the skill and its routines.

## Routine specification:

A routine is a Python `main` function that takes a `RunContext`, `routine_state`, `emit`, `run`, and `ask_user` as arguments. The function can return anything. Here's what the required arguments can be used for:

- context: The context of the conversation. You can use this to get information about the user's goal and the current state of the conversation. The context has the following attributes:
  - session_id: str - A unique identifier for the session. This is useful for tracking the conversation.
  - run_id: str - A unique identifier for the run. This is useful for tracking the conversation.
  - run_drive: Drive - A drive object that can be used to read and write files to a particular location. This is useful for storing data that needs to persist between sessions.
  - skills: dict[str, Skill] - A dictionary of skills that are available to the routine. Each skill has a name and a function that can be used to run the skill.
  - log(dict[str, Any]): A function that can be used to log metadata about the conversation. This is our primary logging mechanism. Metadata must be serializable.
- routine_state: dict[str, Any] - A dictionary that can be used to store state between steps in the routine. This is useful for maintaining context between messages.
- emit(EventProtocol) - A function that can be used to emit messages to the user. This is useful for asking the user for input or providing updates on the progress of the routine. EventProtocol must be one of the following (can be imported from the `events` package):
  - StatusUpdatedEvent(message="something")  // Communicates what the routine is currently doing.
  - MessageEvent(message="something")        // Passed on to the user as a chat message.
  - InformationEvent(message="something")    // Displayed to the user for informational purposes, but not kept in the chat history.
  - ErrorEvent(message="something")          // Indicates to the user that something went wrong.
- run: A function that can be used to run any routine. This is useful for breaking up a large routine into smaller, more manageable pieces. A list of all available routines is provided below.
- ask_user: A function that can be used to ask the user for input. This is useful for getting information from the user that is needed to complete the routine.

The routine function can then have any number of additional arguments (args or kwargs). These arguments can be used to pass in data that is needed to complete the routine.


## Type information

```
LanguageModel = AsyncOpenAI | AsyncAzureOpenAI

AskUserFn = Callable[[str], Awaitable[str]]
ActionFn = Callable[[RunContext], Awaitable[Any]]
EmitFn = Callable[[EventProtocol], None]

class RunRoutineFn(Protocol):
    async def __call__(self, designation: str, *args: Any, **kwargs: Any) -> Any: ...
```

## Available skills and thier configuration

{{skills}}


## Available routines

{{routines}}


## Instructions

Your job is to respond to a user's description of their goal by returning a routine that satisfies the goal. Respond with the routine, delimited by markdown python triple backticks.


## Examples

### A simple example

``` story_unboringer.py

from typing import Any, Optional, cast

from .types import RunContext, EmitFn, RunRoutineFn, AskUserFn
from events import StatusUpdatedEvent, MessageEvent, InformationEvent, ErrorEvent

async def main(
    context: RunContext,
    routine_state: dict[str, Any],
    emit: EmitFn,
    run: RunRoutineFn,
    ask_user: AskUserFn,
    another_arg: str,
) -> str:
    """
    Docstrings are extracted and used as the routine description. This is useful for
    providing additional context to the user about what the routine does, so always
    add an informative one for the routine function.
    """

    # Skills can be configured. Configured attributed can be used in the routine by referencing any skill instance from the context.
    common_skill = cast(CommonSkill, context.skills["common"])
    language_model = common_skill.language_model

    story = ask_user("Tell me a story.")
    emit(StatusUpdatedEvent(message="Summarizing the story..."))
    summarization = run("common.summarize", content=story)
    context.log("story unboringer", {"story": story, "summarization": summarization})

    return f"That's a long story... if I heard you right, you're saying: {summarization}"
```

### An example of using a language model

If you need to use a language model, it will be passed into the skill as a configuration item. You should use our openai_client to make calls to the language model.

```
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

DEFAULT_MAX_SUMMARY_LENGTH = 5000

async def main(
    context: RunContext,
    routine_state: dict[str, Any],
    emit: EmitFn,
    run: RunRoutineFn,
    ask_user: AskUserFn,
    content: str,
    aspect: Optional[str] = None,
    max_length: Optional[int] = DEFAULT_MAX_SUMMARY_LENGTH,
) -> str:
    """
    Summarize the content from the given aspect. The content may be relevant or
    not to a given aspect. If no aspect is provided, summarize the content as
    is.
    """
    common_skill = cast(CommonSkill, context.skills["common"])
    language_model = common_skill.config.language_model

    system_message = "You are a summarizer. Your job is to summarize the content provided by the user. Don't lose important information."
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
        summary = message_content_from_completion(completion)
        metadata["summary"] = summary
        return summary
    finally:
        context.log("summarize", metadata)
```

'''


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

    skill_configs = []
    for skill in context.skills.values():
        skill_configs.append(skill.config.model_dump())

    system_prompt = format_with_liquid(SYSTEM_PROMPT, {"routines": context.routine_usage(), "skills": skill_configs})
    completion_args = {
        "model": "gpt-4o",
        "messages": [
            create_system_message(system_prompt),
            create_user_message(
                goal,
            ),
        ],
    }
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
        emit(MessageEvent(message=routine))
        return routine
    finally:
        context.log("generate_routine", metadata)
