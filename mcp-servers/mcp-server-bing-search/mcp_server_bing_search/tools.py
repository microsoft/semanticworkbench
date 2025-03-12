# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Callable

from mcp.server.fastmcp import Context

from mcp_server_bing_search import settings
from mcp_server_bing_search.types import Link, WebResult
from mcp_server_bing_search.utils import embarrassingly_parallel_async, format_web_results, lookup_url
from mcp_server_bing_search.web.process_website import process_website
from mcp_server_bing_search.web.search_bing import search_bing


async def _process_websites(
    urls: list[str],
    context: Context | None = None,
    chat_completion_client: Callable[..., Any] | None = None,
) -> str:
    """
    Process a list of URLs to extract and format web content.

    Returns:
        A formatted string containing web content suitable for LLM consumption.
    """
    if not urls:
        return "No results found."

    processed_web_results: list[WebResult] = []
    if settings.concurrency_limit > 1:
        processed_web_results = await embarrassingly_parallel_async(
            func=process_website,
            args_list=[
                (
                    Link(url=url),
                    context,
                    chat_completion_client,
                    settings.improve_with_sampling,
                )
                for url in urls
            ],  # type: ignore
            concurrency_limit=settings.concurrency_limit,
        )
    else:
        for url in urls:
            processed_result = await process_website(
                website=Link(url=url),
                context=context,
                chat_completion_client=chat_completion_client,
                apply_post_processing=settings.improve_with_sampling,
            )
            processed_web_results.append(processed_result)

    # Filter out any None or empty results
    web_results = [result for result in processed_web_results if result and result.content]

    if not web_results:
        return "No content could be extracted from the provided URLs."

    # TODO: Deduplicating links across all results

    # Format the results into an LLM-friendly string
    formatted_results = format_web_results(web_results)
    return formatted_results


async def search(
    query: str, context: Context | None = None, chat_completion_client: Callable[..., Any] | None = None
) -> str:
    """
    Search for web results using the provided query and token limit.

    Returns:
        A formatted string containing web search results suitable for LLM consumption.
    """
    search_results = search_bing(query)

    if not search_results:
        return "No results found."

    urls = [result.url for result in search_results]
    return await _process_websites(urls, context, chat_completion_client)


async def click(
    hashes: list[str], context: Context | None = None, chat_completion_client: Callable[..., Any] | None = None
) -> str:
    """
    Looks up each of the hashes to get the associated URLs and then processes the URLs.

    Returns:
        A formatted string containing the processed web content for LLM consumption
    """
    # Look up URLs for each hash
    urls = []
    for url_hash in hashes:
        url = lookup_url(url_hash)
        if url:
            urls.append(url)

    # Only use the max num_search_results amount of urls
    urls = urls[: settings.num_search_results]

    if not urls:
        return "No results found."

    return await _process_websites(urls, context, chat_completion_client)
