from typing import Any

from openai_client import (
    CompletionError,
    format_with_liquid,
)
from skill_library import AskUserFn, EmitFn, RunContext, RunRoutineFn
from skill_library.logging import logger

ASPECT_PROMPT = """
We are conducting thorough research on:
{{TOPIC}}

Our research plan:

```
{{PLAN}}
```

Verified facts so far:

```
{{FACTS}}
```

Previous observations:

```
{{OBSERVATIONS}}
```

When summarizing this page:
1. Extract only verifiable information relevant to our research gaps
2. Include specific technical details, specifications, and quantitative data
3. Note the reliability of the source and any potential biases
4. Distinguish between factual statements and opinions/claims
5. Preserve original terminology and measurements for accuracy
6. Identify information that contradicts our current understanding
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
    urls: list[str] = [],
) -> str:
    """Gather the content from a list of URLs and summarize them according to a particular research project."""

    aspect = format_with_liquid(
        ASPECT_PROMPT, vars={"TOPIC": topic, "PLAN": plan, "FACTS": facts, "OBSERVATIONS": "\n- ".join(observations)}
    )

    metadata = {}
    results = {}
    for url in urls[:3]:
        try:
            content = await run("common.get_content_from_url", url, 10000)
        except CompletionError as e:
            logger.error(f"Error getting content from {url}: {e}")
            metadata[url] = {"fetch error": str(e)}
            continue

        try:
            summary = await run("common.summarize", content=content, aspect=aspect)
        except CompletionError as e:
            logger.error(f"Error summarizing content from {url}: {e}")
            metadata[url] = {"summarization error": str(e)}
            continue

        results[url] = summary
        metadata[url] = {"summary": summary}

    context.log("visit_pages", metadata)
    return "\n\n".join([f"URL: {url}\nSummary: {summary}" for url, summary in results.items()])
