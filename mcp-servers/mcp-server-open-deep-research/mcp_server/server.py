from mcp.server.fastmcp import FastMCP


from . import settings
from .open_deep_research import perform_deep_research

# Set the name of the MCP server
server_name = "Open Deep Research MCP Server"

def create_mcp_server() -> FastMCP:

    # Initialize FastMCP with debug logging.
    mcp = FastMCP(name=server_name, log_level=settings.log_level)

    # Define each tool and its setup.

    @mcp.tool()
    async def deep_research(context: str, request: str) -> str:
        """
        A team member that will deeply research across the internet to answer your question.
        Ask them for all your questions that require browsing the web. Provide them as much
        context as possible, in particular if you need to research on a specific timeframe!
        And don't hesitate to provide them with a complex research task, like analyzing the
        difference between two products, or finding a discrepancy between two sources.
        Your request must be real sentences, not search terms! Like "Research current trends
        for (...)" rather than a few keywords.
        """

        return perform_deep_research("o1", f"Context:\n{context}\n\nRequest:\n{request}")

    return mcp
