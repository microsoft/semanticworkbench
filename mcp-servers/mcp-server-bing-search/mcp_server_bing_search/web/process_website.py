# Copyright (c) Microsoft. All rights reserved.

import asyncio
import io
import logging
import re
from urllib.parse import urljoin, urlparse

from markitdown import MarkItDown

from mcp_server_bing_search import settings
from mcp_server_bing_search.types import Link, WebResult
from mcp_server_bing_search.utils import TokenizerOpenAI
from mcp_server_bing_search.web.get_content import get_raw_web_content
from mcp_server_bing_search.web.llm_processing import clean_content, filter_links

logger = logging.getLogger(__name__)


def sync_filter_links(
    content: str,
    links: list[Link],
    max_links: int,
) -> list[Link]:
    return asyncio.run(
        filter_links(
            content=content,
            links=links,
            max_links=max_links,
        )
    )


def sync_clean_content(
    content: str,
) -> str:
    return asyncio.run(
        clean_content(
            content=content,
        )
    )


async def process_website(
    website: Link,
    apply_post_processing: bool = True,
) -> WebResult:
    raw_content = await get_raw_web_content(url=website.url)

    if not raw_content:
        return WebResult(url=website.url, title="", content="", links=[])

    # Convert the raw HTML to Markdown
    md = MarkItDown(enable_plugins=False)
    buffer = io.BytesIO(raw_content.encode("utf-8"))
    result = md.convert_stream(
        buffer,
        mimetype="text/html",
        charset="utf-8",
    )

    tokenizer = TokenizerOpenAI(model="gpt-4o")

    title = ""
    if result.title:
        title = result.title

    content = ""
    if result.text_content:
        content = result.text_content
        content = tokenizer.truncate_str(content, 60000)
    else:
        return WebResult(
            url=website.url,
            title=title,
            content="",
            links=[],
        )

    links = extract_links_from_markdown(content, base_url=website.url)[0:200]

    web_result = WebResult(
        url=website.url,
        title=title,
        content=content,
        links=links,
    )

    # Apply post-processing if enabled
    if apply_post_processing and settings.improve_with_sampling:
        tasks = []
        task_types = []
        # Filter links with LLM if content and links exist
        if content and links:
            tasks.append(
                asyncio.to_thread(
                    sync_filter_links,
                    content=content,
                    links=links,
                    max_links=settings.max_links,
                )
            )
            task_types.append("filter_links")

        # Clean content using LLM if content exists
        if content:
            tasks.append(
                asyncio.to_thread(
                    sync_clean_content,
                    content=content,
                )
            )
            task_types.append("clean_content")

        if tasks:
            results = await asyncio.gather(*tasks)
            for task_type, result in zip(task_types, results):
                if task_type == "filter_links" and result is not None:
                    web_result.links = result
                elif task_type == "clean_content" and result is not None:
                    web_result.content = result
    return web_result


def extract_links_from_markdown(markdown_content: str, base_url: str | None = None) -> list[Link]:
    """
    Extracts URLs from markdown content, focusing on inline markdown links.

    Args:
        markdown_content: String containing markdown text

    Returns:
        List of extracted URLs from inline markdown links
    """

    # Pattern to match markdown inline links: [text](url)
    inline_link_pattern = r"\[.+?\]\((.+?)\)"

    # Extract inline links
    inline_urls = re.findall(inline_link_pattern, markdown_content)

    # Convert relative URLs to absolute URLs if base_url is provided
    if base_url:
        parsed_base = urlparse(base_url)
        base_scheme = parsed_base.scheme or "https"
        base_netloc = parsed_base.netloc

        processed_urls = []
        for url in inline_urls:
            parsed_url = urlparse(url)
            # If the URL has no scheme or netloc, it's relative
            if not parsed_url.scheme and not parsed_url.netloc:
                # For URLs starting with '/', join with the base domain
                absolute_url = urljoin(f"{base_scheme}://{base_netloc}", url)
                processed_urls.append(absolute_url)
            else:
                processed_urls.append(url)
        inline_urls = processed_urls

    # Remove duplicates while preserving order
    unique_urls = []
    for url in inline_urls:
        if url not in unique_urls:
            unique_urls.append(url)

    # Filter out URLs greater than 300 chars
    unique_urls = [url for url in unique_urls if len(url) <= 300]
    # Filter out any URLs that start with #
    unique_urls = [url for url in unique_urls if not url.startswith("#")]

    # Create Link objects with unique IDs
    unique_urls = [Link(url=url) for url in unique_urls]

    return unique_urls
