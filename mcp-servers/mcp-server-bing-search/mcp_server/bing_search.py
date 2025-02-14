import requests
from .config import Settings

def search_bing(query: str) -> list:
    subscription_key = Settings.bing_search_api_key
    endpoint = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    params = {"q": query}

    try:
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()  # Raise HTTPError for bad responses
        search_results = response.json()

        results = []
        if "webPages" in search_results:
            for item in search_results["webPages"].get("value", []):
                results.append({
                    "name": item.get("name", "No name available"),
                    "url": item.get("url", "No URL available"),
                    "snippet": item.get("snippet", "No snippet available"),
                })
        return results

    except Exception as e:
        print("Error during Bing Search API request:", str(e))
        return []
