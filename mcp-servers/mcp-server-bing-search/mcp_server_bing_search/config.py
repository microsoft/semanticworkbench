# Copyright (c) Microsoft. All rights reserved.

import os
from pathlib import Path
from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings

log_level = os.environ.get("LOG_LEVEL", "INFO")

TEMP_DIR = Path(__file__).parents[1] / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)
MKITDOWN_TEMP = TEMP_DIR / "mkitdown"
MKITDOWN_TEMP.mkdir(parents=True, exist_ok=True)

URL_CACHE_FILE = TEMP_DIR / "cache" / "url_cache.json"


class Settings(BaseSettings):
    log_level: str = log_level
    dev: bool = True
    bing_search_api_key: Annotated[str, Field(validation_alias="BING_SEARCH_API_KEY")] = ""
    azure_endpoint: Annotated[str | None, Field(validation_alias="ASSISTANT__AZURE_OPENAI_ENDPOINT")] = None
    mkitdown_temp: Path = MKITDOWN_TEMP
    url_cache_file: Path = URL_CACHE_FILE
    num_search_results: int = 4
    max_links: int = 25
    improve_with_sampling: bool = True
