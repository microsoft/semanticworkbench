import os
from typing import Any, Optional, cast

import requests
from dotenv import load_dotenv
from skill_library import AskUserFn, EmitFn, RunContext, RunRoutineFn
from skill_library.skills.common.common_skill import CommonSkill


async def main(
    context: RunContext,
    routine_state: dict[str, Any],
    emit: EmitFn,
    run: RunRoutineFn,
    ask_user: AskUserFn,
    q: str,
    num_results: Optional[int] = 7,
) -> list[str]:
    """Search Bing with the given query, return the first num_results URLs."""

    common_skill = cast(CommonSkill, context.skills["common"])
    subscription_key = common_skill.config.bing_subscription_key
    search_url = common_skill.config.bing_search_url or "https://api.bing.microsoft.com/v7.0/search"

    # Load Bing config from environment variables (backwards compat for old code).
    if not subscription_key:
        load_dotenv()
        subscription_key = os.getenv("BING_SUBSCRIPTION_KEY")
        if not subscription_key:
            raise Exception("BING_SUBSCRIPTION_KEY not found in .env.")
        search_url = search_url or os.getenv("BING_SEARCH_URL") or "https://api.bing.microsoft.com/v7.0/search"

    # Search Bing.
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    params = {"q": q}

    try:
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        key_hint = f"{subscription_key[0:3]}...{subscription_key[-3:]}"
        context.log("Error during Bing search.", {"exception": e.strerror, "url": search_url, "key": key_hint})
        raise e

    # Unpack results.
    search_results = response.json()
    values = search_results.get("webPages", {}).get("value", "")
    urls = [str(v["url"]) for v in values]

    # Limit number of results.
    if num_results:
        urls = urls[:num_results]

    return urls
