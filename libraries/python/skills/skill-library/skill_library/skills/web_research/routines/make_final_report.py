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
from skill_library.skills.web_research.research_skill import WebResearchSkill

SYSTEM_PROMPT = """
Consolidate this research for this topic:

`{{TOPIC}}`

into a comprehensive, transparent report.

Your consolidated report should:
1. Clearly distinguish between verified facts and inferences
2. Include source information for key claims
3. Explicitly acknowledge information gaps and limitations
4. Maintain the technical precision of the original content
5. Organize information logically while preserving all substantive content
6. Use confidence indicators (Highly Confident/Moderately Confident/Uncertain) for key findings

Structure the final report with:
1. Summary: A concise summary of key findings
2. Report: Comprehensive findings with clear source attribution
3. Additional Context: Limitations, alternative interpretations, and areas needing further research
4. Sources Consulted: Include all sources that were used in the research, properly cited

When referencing sources in your detailed findings, use numbered citations [1], [2], etc. with proper markdown links that correspond to the Sources Consulted section.

Respond with just your consolidated report without unnecessary commentary.
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

    research_skill = cast(WebResearchSkill, context.skills["web_research"])
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
