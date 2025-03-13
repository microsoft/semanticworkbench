# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging

import requests

logger = logging.getLogger(__name__)


async def get_raw_web_content(url: str) -> str:
    """
    Fetches raw web content from a given URL using requests.

    Uses asyncio.to_thread to make the synchronous requests call non-blocking.
    Returns an empty string if any errors occur.

    Args:
        url: The URL to fetch content from.

    Returns:
        str: The raw web content as a string, or empty string on error.
    """
    try:
        response = await asyncio.to_thread(
            requests.get,
            url,
            timeout=10,
        )
        response.raise_for_status()
        return response.text

    except requests.RequestException as e:
        logger.error(f"Failed to get web content: {e}")
        return ""
    except Exception as e:
        logger.error(f"Unexpected error fetching web content: {e}")
        return ""
