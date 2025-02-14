import requests
import math
from . import settings

def search_bing(query: str, count: int = 10, offset: int = 0) -> str:
    subscription_key = settings.bing_search_api_key
    endpoint = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    params = {"q": query, "count": count, "offset": offset}

    try:
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()  # Raise HTTPError for bad responses
        search_results = response.json()

        # Compute current page number based on offset and count.
        page_num = (offset // count) + 1
        total_estimated_matches = search_results.get("webPages", {}).get("totalEstimatedMatches")
        if total_estimated_matches is not None:
            total_pages = math.ceil(total_estimated_matches / count)
            # Format large numbers for better readability.
            def format_number(n):
                if n >= 1e6:
                    return f"{n/1e6:.2f}M"
                elif n >= 1e3:
                    return f"{n/1e3:.2f}K"
                else:
                    return str(n)

            formatted_matches = format_number(total_estimated_matches)
            formatted_pages = format_number(total_pages)
            header = (
                f"Search Results: Page {page_num} of {formatted_pages} pages "
                f"(Total estimated matches: {formatted_matches})"
            )
        else:
            header = f"Search Results: Page {page_num}"

        text_lines = [header]
        if "webPages" in search_results:
            for i, item in enumerate(search_results["webPages"].get("value", [])):
                # Build readable format
                title = item.get("name", "No title")
                url = item.get("url", "No URL")
                snippet = item.get("snippet", "").strip().replace("\n", " ")
                if len(snippet) > 150:
                    snippet = snippet[:147] + "..."
                text_lines.append(f"\nResult {i + 1}:")
                text_lines.append(f"  Title: {title}")
                text_lines.append(f"  URL:   {url}")
                text_lines.append(f"  Snippet: {snippet}")

        final_output = "\n".join(text_lines)
        return final_output

    except Exception as e:
        print("Error during Bing Search API request:", str(e))
        return "Error during Bing Search API request: " + str(e)
