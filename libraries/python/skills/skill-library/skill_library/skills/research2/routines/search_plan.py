from typing import Any, cast

from openai_client import (
    CompletionError,
    create_assistant_message,
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
from skill_library.skills.research2.research_skill import ResearchSkill

INITIAL_SYSTEM_PROMPT = """
You are a world expert at making efficient plans to solve any task using a set of carefully crafted tools.

Now for the given task, develop a step-by-step high-level plan taking into account the above inputs and list of facts.
This plan should involve individual tasks based on the available tools, that if executed correctly will yield the correct answer.
Do not skip steps, do not add any superfluous steps. Only write the high-level plan.

Here is your topic:

{TOPIC}

List of facts that you know:

{FACTS}

Now begin! Write your plan below.
"""

UPDATE_SYSTEM_PROMPT = """
You're still working towards completing this research:

{TOPIC}

Now for the given topic, develop a step-by-step high-level plan taking into account the above inputs and list of facts.
This plan should involve individual tasks that if executed correctly will yield the correct answer.

If you decide that the research topic has been completed, respond only with <DONE>.
"""


async def main(
    context: RunContext,
    routine_state: dict[str, Any],
    emit: EmitFn,
    run: RunRoutineFn,
    ask_user: AskUserFn,
    topic: str,
    plan: str = "",
    facts: str = "",
    observations: list[str] = [],
) -> tuple[str, bool]:
    """Make a search plan for a research project."""

    research_skill = cast(ResearchSkill, context.skills["common"])
    language_model = research_skill.config.language_model

    system_prompt = UPDATE_SYSTEM_PROMPT if plan else INITIAL_SYSTEM_PROMPT

    completion_args = {
        "model": "gpt-4o",
        "messages": [
            create_system_message(
                format_with_liquid(system_prompt, vars={"TOPIC": topic, "FACTS": facts}),
            ),
            create_user_message(
                f"Topic: {topic}",
            ),
        ],
    }

    if plan:
        completion_args["messages"].append(
            create_assistant_message(
                f"Plan: {plan}",
            )
        )

    if facts:
        completion_args["messages"].append(
            create_assistant_message(
                f"Here is the up-to-date list of facts that you know:: \n```{facts}\n```\n",
            )
        )

    if observations:
        all_observations = "\n- ".join(observations)
        completion_args["messages"].append(
            create_assistant_message(
                f"Observations: \n```{all_observations}\n```\n",
            )
        )

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
        content = message_content_from_completion(completion).strip().strip('"')
        metadata["content"] = content
        if "<DONE>" in content:
            return content, True
        return content, False
    finally:
        context.log("search_plan", metadata)
