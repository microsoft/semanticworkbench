from typing import Optional

from mcp.server.fastmcp import Context, FastMCP

from mcp_server.sampling import perform_sampling

from . import settings
from .giphy_search import perform_search

# Set the name of the MCP server
server_name = "GIPHY MCP Server"


def create_mcp_server() -> FastMCP:
    # Initialize FastMCP with debug logging.
    mcp = FastMCP(name=server_name, log_level=settings.log_level)

    @mcp.tool()
    async def giphy_search(context: str, search_term: str, ctx: Context) -> Optional[dict]:
        """
        A specialized team member that searches the GIPHY database for GIFs based on your search term.
        Use them to find the perfect GIF to express your thoughts or feelings. Provide as much context
        as possible to help them understand the context of your search. Your search term should be a
        specific keyword or phrase that describes the GIF you're looking for. For context, pass as
        much background as you can: if using this tool in a conversation, include the conversation
        history; if in a broader context, include any relevant documents or details. If there is no
        context, pass “None.”
        """

        await ctx.session.send_log_message(
            level="info",
            data="searching...",
        )

        # Perform search using context and search term
        search_results = await perform_search(search_term=search_term, ctx=ctx)

        if not search_results:
            return None

        # Create sampling request message, integrating search results and context
        sampling_result = await perform_sampling(
            context=context,
            search_results=search_results,
            ctx=ctx,
        )

        if sampling_result.type == "image":
            return {
                "data": sampling_result.data,
                "mimeType": sampling_result.mimeType,
            }
        else:
            return {
                "text": sampling_result.text,
            }

    return mcp
