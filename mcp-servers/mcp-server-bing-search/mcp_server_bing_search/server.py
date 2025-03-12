# Copyright (c) Microsoft. All rights reserved.

from mcp.server.fastmcp import Context, FastMCP

from mcp_server_bing_search import settings
from mcp_server_bing_search.tools import click as click_tool
from mcp_server_bing_search.tools import search as search_tool

# Set the name of the MCP server
server_name = "Bing Search MCP Server"


def create_mcp_server() -> FastMCP:
    settings.dev = False

    # Initialize FastMCP with debug logging.
    mcp = FastMCP(name=server_name, log_level=settings.log_level)

    # Define each tool and its setup.
    @mcp.tool()
    async def search(query: str, ctx: Context) -> str:
        """
        Search for web results based on the provided query. Returns the content of the websites found.
        It will provide a list of links with unique hashes for each link. These can be used to identify URLs to go to using the click tool. You should not discuss these links with the user.
        """
        result = await search_tool(query, context=ctx)
        return result

    @mcp.tool()
    async def click_link(hashes: list[str], ctx: Context) -> str:
        """
        "Clicks" the links identified by provided hashes. The hashes are unique identifiers for each link from the search tool.
        """
        result = await click_tool(hashes, context=ctx)
        return result

    return mcp
