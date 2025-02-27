# Sampling Functionality

import base64
from typing import Dict, List

import aiohttp
from mcp.server.fastmcp import Context
from mcp.types import ImageContent, SamplingMessage, TextContent
from mcp_extensions import send_sampling_request


async def perform_sampling(
    context: str, search_results: List[Dict], fastmcp_server_context: Context
) -> ImageContent | TextContent:
    """Perform sampling using search results and context."""

    async def fetch_image_data(image_url: str) -> bytes:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                response.raise_for_status()
                return await response.read()

    async def get_image_content(result: Dict) -> ImageContent:
        image_url = result["images"]["original"]["url"]

        # fetch the image from the search result
        image_data = await fetch_image_data(image_url)

        # encode the image data as base64
        image_data_base64 = base64.b64encode(image_data).decode("utf-8")

        return ImageContent(
            type="image",
            data=f"data:image/gif;base64,{image_data_base64}",
            mimeType="image/gif",
        )

    # Send sampling request to FastMCP server
    sampling_result = await send_sampling_request(
        fastmcp_server_context=fastmcp_server_context,
        messages=[
            SamplingMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"context: {context}",
                ),
            ),
            *[
                SamplingMessage(
                    role="assistant",
                    content=await get_image_content(result),
                )
                for result in search_results
            ],
        ],
        system_prompt="Choose the most fitting image based on user context and search results.",
        max_tokens=100,
    )

    return sampling_result.content
