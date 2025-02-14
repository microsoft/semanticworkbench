from mcp.server.fastmcp import FastMCP


from . import settings
from .bing_search import search_bing

# Set the name of the MCP server
server_name = "Bing Search MCP Server"

def create_mcp_server() -> FastMCP:

    # Initialize FastMCP with debug logging.
    mcp = FastMCP(name=server_name, log_level=settings.log_level)

    # Define each tool and its setup.

    # Example tool
    @mcp.tool()    
    async def echo(value: str) -> str:
        """
        Will return whatever is passed to it.
        """

        return value

    # Bing Web Search tool
    @mcp.tool()
    async def bing_search(query: str) -> list[dict]:
        """
        Search the web using Bing API and return results.
        """
        return search_bing(query)

    return mcp
