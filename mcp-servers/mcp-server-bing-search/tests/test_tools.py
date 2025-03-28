# Copyright (c) Microsoft. All rights reserved.
import pytest

import time

from mcp_server_bing_search.tools import click, search
from mcp_server_bing_search import settings


@pytest.fixture(autouse=True)
def check_config_fixture() -> None:
    if not settings.azure_endpoint:
        pytest.skip("Azure endpoint not set in settings.")

    if not settings.bing_search_api_key:
        pytest.skip("Bing Search API key not set in settings.")


async def test_search() -> None:
    start_time = time.time()
    results = await search(
        "github typescript",
    )
    end_time = time.time()
    response_duration = round(end_time - start_time, 4)
    print(results)
    print(f"Processed search in {response_duration} seconds.")


async def test_click() -> None:
    results = await search(
        "Microsoft",
    )
    # Assumes this finds "https://www.microsoft.com/en-us/"
    results = await click(["a1567f190464"])

    print(results)
