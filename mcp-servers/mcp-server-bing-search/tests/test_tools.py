# Copyright (c) Microsoft. All rights reserved.

import time

from mcp_server_bing_search.tools import click, search


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
