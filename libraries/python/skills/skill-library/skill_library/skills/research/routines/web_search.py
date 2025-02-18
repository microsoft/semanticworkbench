"""
web research skill
"""

import json
from typing import Any

from skill_library import AskUserFn, EmitFn, RunContext, RunRoutineFn


async def main(
    context: RunContext,
    routine_state: dict[str, Any],
    emit: EmitFn,
    run: RunRoutineFn,
    ask_user: AskUserFn,
    search_description: str,
    previous_searches: list[tuple[str, str]] | None = None,
) -> str:
    """
    Bing search using the search_description. Returns summarized web content
    from the top web search results to specifically answer the search
    description. Only necessary for facts and info not contained in GPT-4.

    Sometimes the search queries that are generated internally are not good
    enough to satisfy the search description. If this is the case, you can use
    the previous_searches parameter to provide the search queries that were
    generated previously and the explanation of why the results that were
    obtained from them weren't good enough. This will help the model to generate
    a better search query.
    """

    # Generate search query.
    search_query = await run("research.generate_search_query", search_description, previous_searches or [])

    # Search Bing.
    urls = await run("common.bing_search", search_query)

    # Summarize page content from each search result.
    metadata = {}
    results = {}
    for url in urls:
        content = await run("common.get_content_from_url", url, 10000)
        summary = await run("common.summarize", content=content, aspect=search_description)
        results[url] = summary
        metadata[url] = {"summary": summary}

    # Summarize all pages into a final result.
    response = await run("common.consolidate", json.dumps(results, indent=2))
    metadata["consolidated"] = response
    context.log("web_search", metadata)

    return response
