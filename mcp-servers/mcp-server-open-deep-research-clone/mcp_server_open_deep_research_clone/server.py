from mcp.server.fastmcp import Context, FastMCP
from mcp_extensions import send_tool_call_progress

from .config import settings
from .web_research import perform_web_research

# Set the name of the MCP server
server_name = "Web Research MCP Server"


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

    @mcp.tool()
    async def web_research(context: str, request: str, ctx: Context) -> str:
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

        await send_tool_call_progress(ctx, "Researching...", data={"context": context, "request": request})

        async def on_status_update(status: str) -> None:
            await send_tool_call_progress(ctx, status)

        # Make sure to run the async version of the function to avoid blocking the event loop.
        deep_research_result = await perform_web_research(
            question=f"Context:\n{context}\n\nRequest:\n{request}", on_status_update=on_status_update
        )
        return deep_research_result

    return mcp
