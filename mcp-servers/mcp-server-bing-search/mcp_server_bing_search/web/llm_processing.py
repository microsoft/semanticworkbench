# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Callable

from mcp.server.fastmcp import Context
from mcp_extensions.llm.chat_completion import chat_completion
from mcp_extensions.llm.helpers import compile_messages
from mcp_extensions.llm.llm_types import ChatCompletionRequest

from mcp_server_bing_search.prompts.clean_website import CLEAN_WEBSITE_MESSAGES
from mcp_server_bing_search.prompts.filter_links import FILTER_LINKS_MESSAGES, LINKS_SCHEMA
from mcp_server_bing_search.types import Link


async def clean_content(
    content: str, context: Context | None, chat_completion_client: Callable[..., Any] | None
) -> str:
    """
    Uses an LLM to return a cleaned and shorter version of the provided content
    """
    messages = compile_messages(CLEAN_WEBSITE_MESSAGES, variables={"content": content})
    response = await chat_completion(
        request=ChatCompletionRequest(
            messages=messages,
            model="gpt-4o",
            max_completion_tokens=4000,
            temperature=0,
        ),
        provider="azure_openai" if context is None else "mcp",
        client=chat_completion_client if context is None else context,  # type: ignore
    )
    cleaned_content = response.choices[0].message.content
    return cleaned_content


async def filter_links(
    content: str,
    links: list[Link],
    max_links: int,
    context: Context | None = None,
    chat_completion_client: Callable[..., Any] | None = None,
) -> list[Link]:
    """
    Uses an LLM with structured outputs to choose the most important links
    """
    # Make a links_str where the they are formatted as: <link id=i>link.url</link>
    # where i is the index of the link in the list
    links_str = ""
    for i, link in enumerate(links):
        links_str += f"<link id={i}>{link.url}</link>\n"
    links_str = links_str.strip()

    messages = compile_messages(
        FILTER_LINKS_MESSAGES,
        variables={"content": content, "max_links": str(max_links), "links": links_str},
    )
    response = await chat_completion(
        request=ChatCompletionRequest(
            messages=messages,
            model="gpt-4o",
            max_completion_tokens=1000,
            structured_outputs=LINKS_SCHEMA,
            temperature=0.4,
        ),
        provider="azure_openai" if context is None else "mcp",
        client=chat_completion_client if context is None else context,  # type: ignore
    )
    chosen_links = response.choices[0].json_message
    if chosen_links:
        chosen_links = chosen_links.get("chosen_links", [])
        # Convert the indices to links
        links = [links[i] for i in chosen_links if 0 <= i < len(links)]
        # Return max_links links
        links = links[:max_links]
        return links

    return []
