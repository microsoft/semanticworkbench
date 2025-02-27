# Giphy Search Functionality

import os
from typing import List, Optional

import requests
from mcp.server.fastmcp import Context
from mcp_extensions import send_tool_call_progress
from pydantic import BaseModel


class GiphyResponse(BaseModel):
    data: List[dict]


async def perform_search(search_term: str, ctx: Context) -> Optional[List[dict]]:
    await send_tool_call_progress(ctx, "searching...")

    api_key = os.getenv("GIPHY_API_KEY")  # Retrieve the GIPHY API Key from the environment
    if not api_key:
        raise ValueError("GIPHY_API_KEY not set in the environment")

    giphy_url = f"https://api.giphy.com/v1/gifs/search?api_key={api_key}&q={search_term}&limit=5"
    response = requests.get(giphy_url)
    if response.status_code == 200:
        return GiphyResponse(**response.json()).data
    else:
        raise Exception("Failed to retrieve Giphy results.")
