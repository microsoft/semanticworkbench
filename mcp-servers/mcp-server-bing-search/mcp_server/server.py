from mcp.server.fastmcp import FastMCP


from . import settings

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

    return mcp
