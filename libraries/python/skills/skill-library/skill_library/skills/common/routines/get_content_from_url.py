import requests
from bs4 import BeautifulSoup
from skill_library import RunContext
from skill_library.types import AskUserFn, EmitFn, GetStateFn, RunRoutineFn, SetStateFn


async def main(
    context: RunContext,
    ask_user: AskUserFn,
    run: RunRoutineFn,
    get_state: GetStateFn,
    set_state: SetStateFn,
    emit: EmitFn,
    url: str,
    max_length: int | None = None,
) -> str:
    """Get the content from a webpage."""

    try:
        response = requests.get(url)
        if response.status_code >= 200 and response.status_code < 300:
            soup = BeautifulSoup(response.text, "html.parser")
            content = soup.get_text(separator="\n", strip=True)
            if max_length and len(content) > max_length:
                return content[:max_length]
            else:
                return content
        else:
            return f"Error: `{response.status_code}`"
    except Exception as e:
        return f"Error: `{e}`"
