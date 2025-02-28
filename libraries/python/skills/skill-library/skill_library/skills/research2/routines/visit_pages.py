from typing import Any

from openai_client import (
    CompletionError,
    format_with_liquid,
)
from skill_library import AskUserFn, EmitFn, RunContext, RunRoutineFn
from skill_library.logging import logger

ASPECT_PROMPT = """
We are conduction a research project on the topic: {TOPIC}

Our research plan is:

```
{PLAN}
```

So far we have gathered the following facts:

```
{FACTS}
```

We have made the following observations:

```
{OBSERVATIONS}
```

We are visiting a page to gather more information about the topic to fill out remaining facts.
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
    return "\n".join([f"{url}: {summary}" for url, summary in results.items()])
