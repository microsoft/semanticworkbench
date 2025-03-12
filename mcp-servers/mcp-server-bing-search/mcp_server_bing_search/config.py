# Copyright (c) Microsoft. All rights reserved.

import os
from pathlib import Path

from pydantic_settings import BaseSettings

log_level = os.environ.get("LOG_LEVEL", "INFO")

TEMP_DIR = Path(__file__).parents[1] / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)
MKITDOWN_TEMP = TEMP_DIR / "mkitdown"
MKITDOWN_TEMP.mkdir(parents=True, exist_ok=True)

URL_CACHE_FILE = TEMP_DIR / "cache" / "url_cache.json"


def load_required_env_var(env_var_name: str) -> str:
    value = os.environ.get(env_var_name, "")
    if not value:
        raise ValueError(f"Missing required environment variable: {env_var_name}")
    return value


# Load required environment variables
bing_search_api_key = load_required_env_var("BING_SEARCH_API_KEY")

# Load optional environment variables
azure_endpoint = os.environ.get("ASSISTANT__AZURE_OPENAI_ENDPOINT", None)


class Settings(BaseSettings):
    log_level: str = log_level
    dev: bool = True
    bing_search_api_key: str = bing_search_api_key
    azure_endpoint: str | None = azure_endpoint
    concurrency_limit: int = 1
    mkitdown_temp: Path = MKITDOWN_TEMP
    url_cache_file: Path = URL_CACHE_FILE
    num_search_results: int = 5
    max_links: int = 25
    improve_with_sampling: bool = True
