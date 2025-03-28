# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import time

from mcp_server_bing_search import settings
from mcp_server_bing_search.types import Link, WebResult
from mcp_server_bing_search.utils import format_web_results, lookup_url
from mcp_server_bing_search.web.process_website import process_website
from mcp_server_bing_search.web.search_bing import search_bing

logger = logging.getLogger(__name__)


def sync_process_website(
    website: Link,
    apply_post_processing: bool = True,
) -> WebResult:
    return asyncio.run(process_website(website, apply_post_processing))


async def _process_websites_parallel(
    urls: list[str],
) -> str:
    tasks = []
    for url in urls:
        tasks.append(asyncio.to_thread(sync_process_website, Link(url=url), settings.improve_with_sampling))

    start_time = time.time()
    results = await asyncio.gather(*tasks)
    end_time = time.time()
    response_duration = round(end_time - start_time, 4)
    logger.info(f"Processed {len(urls)} URLs in {response_duration} seconds.")

    # Filter out any None or empty results
    web_results = [result for result in results if result and result.content]

    if not web_results:
        return "No content could be extracted from the provided URLs."

    web_results = format_web_results(web_results)
    return web_results


async def search(query: str) -> str:
    """
    Searches for web results using the provided query.

    Returns:
        A formatted string containing web search results suitable for LLM consumption.
    """
    search_results = search_bing(query)

    if not search_results:
        return "No results found."

    urls = [result.url for result in search_results]
    results = await _process_websites_parallel(urls)
    return results


async def click(hashes: list[str]) -> str:
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

    results = await _process_websites_parallel(urls)
    return results
