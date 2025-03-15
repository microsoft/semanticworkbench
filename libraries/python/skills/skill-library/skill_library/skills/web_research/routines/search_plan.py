from typing import Any, cast

from openai_client import (
    CompletionError,
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

INITIAL_PROMPT = """
As a research expert, create a strategic search plan for:

`{{TOPIC}}`

Your plan should:
1. Prioritize finding high-quality, authoritative sources over quantity
2. Include specific steps to bypass SEO-optimized content in favor of substantive information
3. Focus on locating genuine expert reviews and authentic user feedback
4. Identify specific technical resources likely to contain verifiable information

Current facts:

```
{{FACTS}}
```

Observations:

```
{{OBSERVATIONS}}
```

If you determine the research is complete, respond only with <DONE>.
Otherwise, provide a step-by-step plan focusing on filling information gaps with reliable sources.
"""

UPDATE_PROMPT = """
You're researching:

`{{TOPIC}}`

Review what we've learned and what gaps remain. Current plan:

```
{{PLAN}}
```

Current facts:

```
{{FACTS}}
```

Observations:

```
{{OBSERVATIONS}}
```

For the next phase of research:
1. Evaluate which sources have proven most reliable so far
2. Identify specific information gaps with the highest priority
3. Target specialized and authoritative sources for remaining questions
4. Develop strategies to find technical details and verified user experiences

If the research topic has been completed with verified information, respond only with <DONE>.
Otherwise, revise your plan to focus on remaining information gaps.
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

    research_skill = cast(WebResearchSkill, context.skills["web_research"])
    language_model = research_skill.config.reasoning_language_model

    if not plan:
        prompt = format_with_liquid(INITIAL_PROMPT, vars={"TOPIC": topic, "FACTS": facts, "OBSERVATIONS": observations})
    else:
        prompt = format_with_liquid(
            UPDATE_PROMPT, vars={"TOPIC": topic, "FACTS": facts, "PLAN": plan, "OBSERVATIONS": observations}
        )

    completion_args = {
        "model": "o3-mini",
        "reasoning_effort": "high",
        "messages": [
            create_user_message(
                prompt,
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
        content = message_content_from_completion(completion).strip().strip('"')
        metadata["content"] = content
        if "<DONE>" in content:
            return content, True
        return content, False
    finally:
        context.log("search_plan", metadata)
