# Copyright (c) Microsoft. All rights reserved.

import json
from collections.abc import Collection, Set
from typing import Literal

import tiktoken

from mcp_server_bing_search import settings
from mcp_server_bing_search.types import Link, WebResult


def lookup_url(url_hash: str) -> str | None:
    """
    Looks up a URL by its hash in the cache file.

    Args:
        url_hash: The URL hash to look up

    Returns:
        The URL associated with the hash, or None if not found
    """
    cache_file = settings.url_cache_file
    if not cache_file.exists():
        return None

    try:
        with cache_file.open("r", encoding="utf-8") as f:
            cache = json.load(f)

        return cache.get(url_hash)
    except (json.JSONDecodeError, IOError):
        return None


def consolidate_links(web_results: list[WebResult]) -> list[Link]:
    """
    Extracts and deduplicates links from a list of web results.

    Args:
        web_results: List of WebResult objects containing links

    Returns:
        A list of unique Link objects across all web results
    """
    unique_links = {}

    for result in web_results:
        for link in result.links:
            if link.unique_id not in unique_links:
                unique_links[link.unique_id] = link

    return list(unique_links.values())


def format_web_results(web_results: list[WebResult]) -> str:
    """
    Creates an LLM friendly representation of the web results.
    """
    unique_links = consolidate_links(web_results)

    formatted_results = ""
    for result in web_results:
        formatted_result = ""
        formatted_result = "<website>\n"
        formatted_result += f"<url>{result.url}</url>\n"
        formatted_result += f"<title>{result.title}</title>\n"
        formatted_result += f"<content>{result.content}\n</content>\n"
        formatted_result += "</website>\n"
        formatted_results += formatted_result

    if unique_links:
        formatted_results += "<links>\n"
        for link in unique_links:
            formatted_results += f"<link id={link.unique_id}>{link}</link>\n"
        formatted_results += "</links>\n"

    return formatted_results.strip()


class TokenizerOpenAI:
    def __init__(
        self,
        model: str,
        allowed_special: Literal["all"] | Set[str] | None = None,
        disallowed_special: Literal["all"] | Collection[str] | None = None,
    ) -> None:
        self.model = model
        self.allowed_special = allowed_special
        self.disallowed_special = disallowed_special

        self.init_tokenizer(model, allowed_special, disallowed_special)

    def init_tokenizer(
        self,
        model: str,
        allowed_special: Literal["all"] | Set[str] | None = None,
        disallowed_special: Literal["all"] | Collection[str] | None = None,
    ) -> None:
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            default_encoding = "o200k_base"
            self.encoding = tiktoken.get_encoding(default_encoding)

        if not allowed_special:
            self.allowed_special = set()
        if not disallowed_special:
            self.disallowed_special = ()

    def truncate_str(self, text: str, max_len: int) -> str:
        tokens = self.encoding.encode(
            text,
            allowed_special=self.allowed_special if isinstance(self.allowed_special, (set, frozenset)) else set(),
            disallowed_special=self.disallowed_special if self.disallowed_special is not None else (),
        )
        if len(tokens) > max_len:
            tokens = tokens[:max_len]
            truncated_text = self.encoding.decode(tokens)
            return truncated_text
        else:
            return text

    def num_tokens_in_str(self, text: str) -> int:
        return len(
            self.encoding.encode(
                text,
                allowed_special=self.allowed_special if isinstance(self.allowed_special, (set, frozenset)) else set(),
                disallowed_special=self.disallowed_special if self.disallowed_special is not None else (),
            )
        )
