from typing import Optional

from mcp.server.fastmcp import Context, FastMCP

from . import settings
from .giphy_search import perform_search

# Set the name of the MCP server
server_name = "GIPHY MCP Server"


def create_mcp_server() -> FastMCP:
    # Initialize FastMCP with debug logging.
    mcp = FastMCP(name=server_name, log_level=settings.log_level)

    @mcp.tool()
    async def giphy_search_tool(context: str, search_term: str, ctx: Context) -> Optional[list]:
        await ctx.session.send_log_message(
            level="info",
            data="searching...",
        )

        # Perform search using context and search term
        search_results = perform_search(context, search_term)

        # Sampling isn't implemented in FastMCP yet, so we'll need to extend it.
        # For now, just return a simplified list.

        return [
            {
                "title": result["title"],
                "alt_text": result["alt_text"],
                "image": result["images"]["original"],
            }
            for result in search_results
        ]

        # # Create sampling request message, integrating search results and context
        # sampling_result = await perform_sampling(search_results, context)

        # # Extract and return image selected by sampling
        # final_image = next(
        #     (content for content in sampling_result if content['type'] == "image"), None)
        # return final_image["data"] if final_image else None

    return mcp
