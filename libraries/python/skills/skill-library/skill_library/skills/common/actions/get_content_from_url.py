import requests
from bs4 import BeautifulSoup
from skill_library import RunContext


async def get_content_from_url(context: RunContext, url: str, max_length: int | None = None) -> str:
    """Get the content from a webpage."""

    response = requests.get(url)
    if response.status_code >= 200 and response.status_code < 300:
        soup = BeautifulSoup(response.text, "html.parser")
        content = soup.get_text(separator="\n", strip=True)
        if max_length and len(content) > max_length:
            return content[:max_length]
        else:
            return content
    else:
        return f"Error: {response.status_code}"


__default__ = get_content_from_url
