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
from skill_library.skills.web_research.research_skill import WebResearchSkill

SYSTEM_PROMPT = """
As a search expert, craft a precise Bing query to find high-quality information for:

{{TOPIC}}

Optimize your query to:
1. Target authoritative sources and technical documentation
2. Bypass SEO-optimized content lacking substantive information
3. Find genuine expert reviews and user feedback
4. Locate specific technical details needed for our research

Use search operators (site:, filetype:, etc.) to target specialized resources and authoritative domains.

Focus your query on the next immediate step in our research plan, specifically addressing information gaps in our current knowledge.

Respond with just the optimized search query - no explanation.
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
    observations: list[str],
) -> list[str]:
    """Perform a search for a research project. Return the top URLs."""

    research_skill = cast(WebResearchSkill, context.skills["web_research"])
    language_model = research_skill.config.language_model

    completion_args = {
        "model": "gpt-4o",
        "messages": [
            create_system_message(
                format_with_liquid(SYSTEM_PROMPT, vars={"TOPIC": topic}),
            ),
            create_user_message(
                f"Topic: {topic}",
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

    query = ""
    urls = []
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
        context.log("search", metadata)
        raise completion_error from e
    else:
        content = message_content_from_completion(completion).strip().strip('"')
        metadata["content"] = content
        query = content

        # Search Bing.
        urls = await run("common.bing_search", query)
        metadata["urls"] = urls

        context.log("search", metadata)
        return urls
