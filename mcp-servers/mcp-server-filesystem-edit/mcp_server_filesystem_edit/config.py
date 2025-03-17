# Copyright (c) Microsoft. All rights reserved.

import os
from pathlib import Path

from pydantic_settings import BaseSettings

log_level = os.environ.get("LOG_LEVEL", "INFO")


def load_required_env_var(env_var_name: str) -> str:
    value = os.environ.get(env_var_name, "")
    if not value:
        raise ValueError(f"Missing required environment variable: {env_var_name}")
    return value


class Settings(BaseSettings):
    log_level: str = log_level
    # TODO: Currently hardcoding the allowed dirs.
    allowed_directories: list[str] = [str(Path(__file__).parents[1] / "temp" / "latex")]

    # LLM and prompt related settings
    comment_author: str = "Feedback Tool"
    doc_editor_prefix: str = "[Document Editor]: "
