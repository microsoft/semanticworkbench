import logging

import httpx

logger = logging.getLogger(__name__)


async def get_raw_web_content(url: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
    except httpx.RequestError as e:
        logger.error(f"Failed to get web content: {e}")
        return ""
    except Exception as e:
        logger.error(f"Unexpected error fetching web content: {e}")
        return ""
