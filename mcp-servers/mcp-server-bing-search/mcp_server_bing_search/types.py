# Copyright (c) Microsoft. All rights reserved.

import hashlib
import json
import threading

from pydantic import BaseModel, Field, model_validator

from mcp_server_bing_search import settings

# Module-level lock for thread safety
_url_cache_lock = threading.Lock()


class Link(BaseModel):
    url: str
    unique_id: str = ""

    @model_validator(mode="before")
    @classmethod
    def set_unique_id(cls, data: dict) -> dict:
        """Automatically hash the URL to create unique_id if not provided."""
        if isinstance(data, dict):
            if "url" in data and (not data.get("unique_id")):
                data["unique_id"] = hash_and_cache_url(data["url"])
        return data


class WebResult(BaseModel):
    url: str
    title: str
    content: str
    links: list[Link] = Field(default_factory=list, description="List of ids that uniquely identify the links")


class SearchResult(BaseModel):
    display_url: str
    url: str
    name: str
    snippet: str


def hash_and_cache_url(url: str) -> str:
    """
    Creates a hash of the given URL and stores that in a lookup file for later.
    Uses a threading lock to ensure thread safety.

    Args:
        url: The URL to hash

    Returns:
        The first 12 characters of the URL's SHA-256 hash in hexadecimal
    """
    cache_file = settings.url_cache_file

    # Create a SHA-256 hash of the URL
    url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]

    # Ensure the cache directory exists
    cache_file.parent.mkdir(parents=True, exist_ok=True)

    with _url_cache_lock:
        # Load existing cache or initialize empty dict
        cache = {}
        if cache_file.exists():
            try:
                with cache_file.open("r", encoding="utf-8") as f:
                    cache = json.load(f)
            except json.JSONDecodeError:
                # If the file exists but is corrupted, start with empty cache
                cache = {}

        # Add the URL to the cache
        cache[url_hash] = url

        # Save the updated cache
        with cache_file.open("w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)

    return url_hash
