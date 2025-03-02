# Sampling Functionality

import asyncio
import base64
import json
import logging
from textwrap import dedent
from typing import Any, Dict, List, Union

from mcp.server.fastmcp import Context
from mcp.types import ImageContent, SamplingMessage, TextContent
from mcp_extensions import send_sampling_request, send_tool_call_progress

from .utils import fetch_url

logger = logging.getLogger(__name__)

# Limit the number of concurrent image fetches
semaphore = asyncio.Semaphore(5)


def get_image_url(result: Dict) -> str | None:
    return result.get("images", {}).get("original", {}).get("url", None)


async def get_image_content_with_limit(result: Dict) -> ImageContent | None:
    async with semaphore:
        image_url = get_image_url(result)
        if image_url is None:
            return None

        try:
            image_data = await fetch_url(image_url)
            image_data_base64 = base64.b64encode(image_data).decode("utf-8")

            return ImageContent(
                type="image",
                data=f"data:image/gif;base64,{image_data_base64}",
                mimeType="image/gif",
            )
        except Exception as e:
            logger.error(f"Failed to fetch image from {image_url}: {str(e)}")
            return None


def get_text_content(result: Dict) -> TextContent | None:
    parts: dict[str, str] = {}
    if "title" in result and len(result["title"].strip()) > 0:
        parts["title"] = result["title"]
    if "alt_text" in result and len(result["alt_text"].strip()) > 0:
        parts["alt_text"] = result["alt_text"]

    image_url = get_image_url(result)
    if image_url is not None:
        parts["url"] = image_url

    if len(parts) == 0:
        return None

    description = ", ".join(parts.values())
    return TextContent(
        type="text",
        text=f"Image: {description}",
    )


async def generate_sampling_messages(search_results: List[Dict]) -> List[SamplingMessage]:
    # Fetch all images concurrently
    image_contents = await asyncio.gather(*[get_image_content_with_limit(result) for result in search_results])

    # Create flattened list of text+image messages
    messages = []
    for result, image_content in zip(search_results, image_contents):
        text_content = get_text_content(result)
        if text_content is not None:
            messages.append(SamplingMessage(role="user", content=text_content))
        if image_content is not None:
            messages.append(SamplingMessage(role="user", content=image_content))
    return messages


async def perform_sampling(
    context: str, search_results: List[Dict[str, Any]], ctx: Context
) -> Union[ImageContent, TextContent]:
    """
    Performs sampling to select the most appropriate image based on context and search results.

    Args:
        context: The user's context/query
        search_results: List of search result dictionaries containing image information
        ctx: Context object for the request

    Returns:
        Either an ImageContent or TextContent object representing the chosen content
    """

    # Send progress update
    await send_tool_call_progress(ctx, "gathering image data...")

    # Insert attachment and history messages to provide additional context
    attachment_messages_variable = json.dumps({"variable": "attachment_messages"})
    history_messages_variable = json.dumps({"variable": "history_messages"})
    messages = [
        SamplingMessage(role="user", content=TextContent(type="text", text=attachment_messages_variable)),
        SamplingMessage(role="user", content=TextContent(type="text", text=history_messages_variable)),
    ]

    # Generate sampling messages
    messages += await generate_sampling_messages(search_results)

    await send_tool_call_progress(ctx, "choosing image...")

    # FIXME add support for structured output to enforce image selection
    # Send sampling request to FastMCP server
    sampling_result = await send_sampling_request(
        fastmcp_server_context=ctx,
        system_prompt=dedent(f"""
            Analyze these images and choose the best choice based on provided context.
            Context: {context}
            Return the url for the chosen image.
        """).strip(),
        messages=messages,
        max_tokens=100,
    )

    return sampling_result.content
