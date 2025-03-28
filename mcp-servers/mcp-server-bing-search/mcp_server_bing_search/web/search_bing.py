# Copyright (c) Microsoft. All rights reserved.

import httpx

from mcp_server_bing_search import settings
from mcp_server_bing_search.types import SearchResult


def search_bing(query: str) -> list[SearchResult]:
    """
    Makes a call to the Bing Web Search API with a query and returns relevant web search.
    Documentation: https://docs.microsoft.com/en-us/bing/search-apis/bing-web-search/overview
    """
    subscription_key = settings.bing_search_api_key
    if not subscription_key:
        raise ValueError("BING_SEARCH_API_KEY is not set in the environment variables.")

    endpoint = "https://api.bing.microsoft.com/v7.0/search"

    mkt = "en-US"
    params = {"q": query, "mkt": mkt, "count": settings.num_search_results}
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(endpoint, headers=headers, params=params)
            response.raise_for_status()
            response_data = response.json()

            results: list[SearchResult] = []
            for web_page in response_data["webPages"]["value"]:
                results.append(
                    SearchResult(
                        display_url=web_page["displayUrl"],
                        url=web_page["url"],
                        name=web_page["name"],
                        snippet=web_page["snippet"],
                    )
                )

            return results
    except Exception as ex:
        raise ex
