# Copyright (c) Microsoft. All rights reserved.

import os
import sys
from typing import Annotated

import pendulum
from pydantic import Field
from pydantic_settings import BaseSettings

log_level = os.environ.get("LOG_LEVEL", "INFO")


def load_required_env_var(env_var_name: str) -> str:
    value = os.environ.get(env_var_name, "")
    if not value:
        raise ValueError(f"Missing required environment variable: {env_var_name}")
    return value


class Settings(BaseSettings):
    log_level: str = log_level
    allowed_directories: list[str] = []
    include_hidden_paths: bool = False
    pdflatex_enabled: bool = False
    office_support_enabled: Annotated[bool, Field(default_factory=lambda: sys.platform == "win32")] = False

    # LLM and prompt related settings
    comment_author: str = "Feedback Tool"
    doc_editor_prefix: str = "[Document Editor]: "
    feedback_tool_prefix: str = "[Feedback Tool]: "
    file_tool_prefix: str = "[File Tool]: "
    rewrite_threshold: int = 250  # Tokens above this will trigger document edits instead of a rewrite

    # Model choices. NOTE: When using MCP sampling, the value here != what might actually be used.
    draft_path_model: str = "gpt-4.1"
    edit_model: str = "o4-mini"
    convert_tool_calls_model: str = "gpt-4.1"
    summarization_model: str = "gpt-4.1"
    comment_model: str = "o4-mini"
    comment_analysis_model: str = "gpt-4.1"
    knowledge_cutoff: str = "2024-05"

    def current_date_func(self) -> str:
        """Return the current date in Eastern US timezone formatted as YYYY-MM-DD."""
        return pendulum.now(tz="America/Los_Angeles").format("YYYY-MM-DD")
