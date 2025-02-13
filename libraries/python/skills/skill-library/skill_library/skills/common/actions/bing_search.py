import os
from typing import Optional

import requests
from dotenv import load_dotenv
from skill_library import RunContext


async def bing_search(context: RunContext, q: str, num_results: Optional[int] = 7) -> list[str]:
    """Search Bing with the given query, return the first num_results URLs."""

    load_dotenv()
    subscription_key = os.getenv("BING_SEARCH_SUBSCRIPTION_KEY")
    if not subscription_key:
        raise Exception("BING_SEARCH_SUBSCRIPTION_KEY not found in .env.")
    search_url = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    params = {"q": q}
    response = requests.get(search_url, headers=headers, params=params)
    response.raise_for_status()
    search_results = response.json()
    values = search_results.get("webPages", {}).get("value", "")
    urls = [str(v["url"]) for v in values]

    if num_results:
        urls = urls[:num_results]

    return urls


__default__ = bing_search
