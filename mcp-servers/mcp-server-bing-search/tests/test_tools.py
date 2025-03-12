from mcp_extensions.llm.openai_chat_completion import openai_client
from mcp_server_bing_search import settings
from mcp_server_bing_search.tools import click, search


async def test_search() -> None:
    client = openai_client(
        api_type="azure_openai",
        azure_endpoint=settings.azure_endpoint,
        aoai_api_version="2025-01-01-preview",
    )
    results = await search(
        "github typescript",
        context=None,
        chat_completion_client=client,
    )
    print(results)


async def test_click() -> None:
    client = openai_client(
        api_type="azure_openai",
        azure_endpoint=settings.azure_endpoint,
        aoai_api_version="2025-01-01-preview",
    )
    results = await search(
        "Microsoft",
        context=None,
        chat_completion_client=client,
    )
    # Assumes this finds "https://www.microsoft.com/en-us/"
    results = await click(["a1567f190464"], context=None, chat_completion_client=client)

    print(results)
