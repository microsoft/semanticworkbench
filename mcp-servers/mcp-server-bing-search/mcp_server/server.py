from mcp.server.fastmcp import FastMCP


from . import settings
from .bing_search import search_bing

# Set the name of the MCP server
server_name = "Bing Search MCP Server"

def create_mcp_server() -> FastMCP:

    # Initialize FastMCP with debug logging.
    mcp = FastMCP(name=server_name, log_level=settings.log_level)

    # Define each tool and its setup.

    # Define the web search tool
    @mcp.tool(name="web_search_tool",
              description="Performs a web search using the Bing Search API, ideal for general queries, news, and articles.")
    async def web_search(query: str, count: int = 10, offset: int = 0) -> list:
        """
        Utilizes the web search tool for general content and recent events.
        """
        return search_bing(query, count, offset)

    return mcp
