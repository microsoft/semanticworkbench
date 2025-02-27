# Giphy Search Functionality

import os
from typing import List

import requests
from pydantic import BaseModel


class GiphyResponse(BaseModel):
    data: List[dict]


def perform_search(context, search_term):
    api_key = os.getenv("GIPHY_API_KEY")  # Retrieve the GIPHY API Key from the environment
    if not api_key:
        raise ValueError("GIPHY_API_KEY not set in the environment")

    giphy_url = f"https://api.giphy.com/v1/gifs/search?api_key={api_key}&q={search_term}&limit=5"
    response = requests.get(giphy_url)
    if response.status_code == 200:
        return GiphyResponse(**response.json()).data
    else:
        raise Exception("Failed to retrieve Giphy results.")
