from typing import Any, cast

from openai_client import (
    CompletionError,
    create_assistant_message,
    create_system_message,
    extra_data,
    format_with_liquid,
    make_completion_args_serializable,
    message_content_from_completion,
    validate_completion,
)
from skill_library import AskUserFn, EmitFn, RunContext, RunRoutineFn
from skill_library.logging import logger
from skill_library.skills.research2.research_skill import ResearchSkill

SYSTEM_PROMPT = """
Please synthesize all the information gathered into a comprehensive report with these sections:

### 1. Task outcome (short version):
[Concise summary of findings about {TASK}]

### 2. Task outcome (extremely detailed version):
[Comprehensive details about partnerships, programs, funding, metrics]

### 3. Additional context (if relevant):
[Background information, limitations, further exploration areas]

Here is your topic:

{TOPIC}

"""


async def main(
    context: RunContext,
    routine_state: dict[str, Any],
    emit: EmitFn,
    run: RunRoutineFn,
    ask_user: AskUserFn,
    topic: str,
    plan: str,
    facts: str,
    observations: list[str] = [],
) -> str:
    """Make a search plan for a research project."""

    research_skill = cast(ResearchSkill, context.skills["common"])
    language_model = research_skill.config.language_model

    completion_args = {
        "model": "gpt-4o",
        "messages": [
            create_system_message(
                format_with_liquid(SYSTEM_PROMPT, vars={"TOPIC": topic}),
            ),
        ],
    }

    completion_args["messages"].append(
        create_assistant_message(
            f"Plan: {plan}",
        )
    )

    completion_args["messages"].append(
        create_assistant_message(
            f"Here is the up-to-date list of facts that you know:: \n```{facts}\n```\n",
        )
    )

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
        return content
    finally:
        context.log("make_final_report", metadata)
