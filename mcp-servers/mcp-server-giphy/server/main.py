# Main entry point for the MCP GIPHY Server

import argparse
from typing import Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from server.giphy_search import perform_search

server_name = "GIPHY MCP Server"

# Load environment variables from .env
load_dotenv()

# Command-line arguments for transport and port
parser = argparse.ArgumentParser(description=f"Run the {server_name}.")
parser.add_argument(
    "--transport",
    default="stdio",
    choices=["stdio", "sse"],
    help="Transport protocol to use ('stdio' or 'sse'). Default is 'stdio'.",
)
parser.add_argument(
    "--port",
    type=int,
    default=8000,
    help="Port to use for SSE (default is 8000)."
)

# Initialize FastMCP with debug logging.
mcp = FastMCP(name=server_name, log_level="DEBUG")

# Define each tool and its setup.


@mcp.tool()
async def giphy_search_tool(context: str, search_term: str) -> Optional[list]:
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


if __name__ == "__main__":
    args = parser.parse_args()
    if args.transport == "sse":
        mcp.settings.port = args.port

    mcp.run(transport=args.transport)
