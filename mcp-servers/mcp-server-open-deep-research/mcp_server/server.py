from mcp.server.fastmcp import Context, FastMCP

from . import settings
from .open_deep_research import perform_deep_research_async

# Set the name of the MCP server
server_name = "Open Deep Research MCP Server"


def create_mcp_server() -> FastMCP:
    # Initialize FastMCP with debug logging.
    mcp = FastMCP(name=server_name, log_level=settings.log_level)

    # Define each tool and its setup.

    @mcp.tool()
    async def deep_research(context: str, request: str, ctx: Context) -> str:
        """
        A specialized team member that thoroughly researches the internet to answer your questions.
        Use them for anything requiring web browsing—provide as much context as possible, especially
        if you need to research a specific timeframe. Don’t hesitate to give complex tasks, like
        analyzing differences between products or spotting discrepancies between sources. Your
        request must be full sentences, not just search terms (e.g., “Research current trends for…”
        instead of a few keywords). For context, pass as much background as you can: if using this
        tool in a conversation, include the conversation history; if in a broader context, include
        any relevant documents or details. If there is no context, pass “None.” Finally, for the
        request itself, provide the specific question you want answered, with as much detail as
        possible about what you need and the desired output.
        """

        await ctx.session.send_log_message(
            level="info",
            data="researching...",
        )

        # Make sure to run the async version of the function to avoid blocking the event loop.
        deep_research_result = await perform_deep_research_async("o1", f"Context:\n{context}\n\nRequest:\n{request}")
        return deep_research_result

    return mcp
