# Giphy Search Functionality

from typing import List, Optional
from .config import settings

import requests
from mcp.server.fastmcp import Context
from mcp_extensions import send_tool_call_progress
from pydantic import BaseModel

from mcp_server.sampling import perform_sampling


class GiphyResponse(BaseModel):
    data: List[dict]


async def perform_search(context: str, search_term: str, ctx: Context) -> Optional[dict]:
    await send_tool_call_progress(ctx, "searching for images...")

    # Perform GIPHY search
    search_results = await search(search_term)

    if not search_results:
        return None

    # Create sampling request message, integrating search results and context
    sampling_result = await perform_sampling(
        context=context,
        search_results=search_results,
        ctx=ctx,
    )

    if sampling_result.type == "image":
        return {
            "data": sampling_result.data,
            "mimeType": sampling_result.mimeType,
        }
    else:
        return {
            "text": sampling_result.text,
        }


async def search(search_term: str) -> Optional[List[dict]]:
    if not settings.giphy_api_key:
        raise ValueError("Giphy API key is not set in the configuration.")

    giphy_url = f"https://api.giphy.com/v1/gifs/search?api_key={settings.giphy_api_key}&q={search_term}&limit=5"
    response = requests.get(giphy_url)
    if response.status_code == 200:
        return GiphyResponse(**response.json()).data
    else:
        raise Exception("Failed to retrieve Giphy results.")
