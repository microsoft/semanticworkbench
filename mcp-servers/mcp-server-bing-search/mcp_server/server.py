from mcp.server.fastmcp import FastMCP


from . import settings
from .bing_search import search_bing
from pydantic import Field
from typing import Annotated
from textwrap import dedent

# Set the name of the MCP server
server_name = "Bing Search MCP Server"

def create_mcp_server() -> FastMCP:

    # Initialize FastMCP with debug logging.
    mcp = FastMCP(name=server_name, log_level=settings.log_level)

    # Define each tool and its setup.

    # Define the web search tool with enriched metadata for LLMs and human users
    @mcp.tool(
        name="web_search_tool",
        description=
            dedent('''
                Performs a web search using the Bing Search API. Accepts a search query along with pagination 
                parameters (count and offset) and returns a plain text summary of results, including a header that shows 
                the current page, total pages, and total estimated matches. Example output:


                Search Results: Page 1 of 964.00K pages (Total estimated matches: 9.64M)


                Result 1:

                  Title: The 10 Biggest AI Trends Of 2025 Everyone Must Be Ready For Today - Forbes

                  URL:   https://www.forbes.com/...

                  Snippet: Discover the 10 major AI trends set to reshape 2025: ...


                Use this tool for retrieving brief summaries and key information about a topic.
            ''').strip()

    )
    async def web_search(
        query: Annotated[str, Field(description="The search query. Supports natural language input (max 400 chars).", max_length=400)],
        count: Annotated[int,
        Field(ge=1,
              le=50,
              description="Number of results per page (default 10).",
              default=10)
        ] = 10,
        offset: Annotated[int,
        Field(ge=0,
              description="The offset into the result set (0 for first page).",
              default=0)
        ] = 0,
    ) -> str:
        return search_bing(query, count, offset)

    return mcp
