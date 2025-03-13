# Copyright (c) Microsoft. All rights reserved.

import asyncio
import concurrent.futures
import json
from collections.abc import Awaitable, Callable, Collection, Set
from typing import Any, Literal

import tiktoken

from mcp_server_bing_search import settings
from mcp_server_bing_search.types import WebResult


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


def format_web_results(web_results: list[WebResult]) -> str:
    """
    Creates an LLM friendly representation of the web results.
    """

    formatted_results = ""
    for result in web_results:
        formatted_result = ""
        formatted_result = "<website>\n"
        formatted_result += f"<url>{result.url}</url>\n"
        formatted_result += f"<title>{result.title}</title>\n"
        formatted_result += f"<content>{result.content}\n</content>\n"
        formatted_result += "<links>\n"
        for link in result.links:
            formatted_result += f"<link id={link.unique_id}>{link}</link>\n"

        formatted_result += "</links>\n"
        formatted_result += "</website>\n"
        formatted_results += formatted_result

    return formatted_results.strip()


class TokenizerOpenAI:
    def __init__(
        self,
        model: str,
        allowed_special: Literal["all"] | Set[str] | None = None,
        disallowed_special: Literal["all"] | Collection[str] | None = None,
    ):
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


async def embarrassingly_parallel_async(
    func: Callable[..., Awaitable[Any]],
    args_list: tuple[tuple[Any, ...], ...] | None = None,
    kwargs_list: list[dict[str, Any]] | None = None,
    concurrency_limit: int = 10,
) -> list[Any]:
    """Execute multiple async functions independently in separate threads.

    Each async function runs in its own thread with its own event loop,
    providing true isolation between tasks.

    Args:
        func: An async function that returns an awaitable
        args_list: A tuple of tuples each containing positional arguments
        kwargs_list: A list of dictionaries containing keyword arguments
        concurrency_limit: Maximum number of threads to use (None means ThreadPoolExecutor default)

    Raises:
        ValueError: If neither args_list nor kwargs_list is provided
        ValueError: If both are provided but have different lengths

    Returns:
        list[Any]: Results from each function call in the order tasks were submitted
    """
    if not args_list and not kwargs_list:
        raise ValueError("Either args_list or kwargs_list must be provided")

    if args_list and kwargs_list and len(args_list) != len(kwargs_list):
        raise ValueError("args_list and kwargs_list must be of the same length")

    def run_async_in_thread(idx: int) -> Any:
        """Run an async function in a new event loop in the current thread."""
        args = args_list[idx] if args_list else ()
        kwargs = kwargs_list[idx] if kwargs_list else {}

        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Run the async function to completion and return the result
            return loop.run_until_complete(func(*args, **kwargs))
        finally:
            # Clean up
            loop.close()

    task_count = len(args_list) if args_list else len(kwargs_list or [])
    results = []

    # Use ThreadPoolExecutor to run each task in a separate thread
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency_limit) as executor:
        # Submit all tasks and collect their futures
        futures = [executor.submit(run_async_in_thread, i) for i in range(task_count)]

        # Retrieve results in the order they were submitted
        for future in concurrent.futures.as_completed(futures):
            try:
                results.append(future.result())
            except Exception as exc:
                results.append(exc)

    return results
