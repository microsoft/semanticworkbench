"""
web research skill
"""

import json

from skill_library import RunContext
from skill_library.types import (
    AskUserFn,
    EmitFn,
    GetStateFn,
    Metadata,
    PrintFn,
    RunActionFn,
    RunRoutineFn,
    SetStateFn,
)


# Define your routine function. We could use a string here, but it's better to
# use a function and then get the source code of that function so we can lint
# it.
async def main(
    context: RunContext,
    ask_user: AskUserFn,
    print: PrintFn,
    run_action: RunActionFn,
    run_routine: RunRoutineFn,
    get_state: GetStateFn,
    set_state: SetStateFn,
    # stack_state_context: StackContext,
    emit: EmitFn,
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

    full_metadata: Metadata = {}

    # Generate search query.
    search_query = await run_action("common.generate_search_query", search_description, previous_searches or [])
    # full_metadata["generate_search_query"] = metadata

    # Search Bing.
    urls = await run_action("common.bing_search", search_query)

    # Summarize page content from each search result.
    results = {}
    debug_i = 0
    for url in urls:
        content = await run_action("common.get_content_from_url", url, 10000)
        summary, metadata = await run_action("common.summarize", search_description, content)
        results[url] = summary
        full_metadata[f"summarize_url_content_{debug_i}"] = metadata

        debug_i += 1

    # Summarize all pages into a final result.
    response, metadata = await run_action("common.summarize", search_description, json.dumps(results, indent=2))
    full_metadata["summarize_all_results"] = metadata

    return response
