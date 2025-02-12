# Main entry point for the MCP GIPHY Server

import argparse
from typing import Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables from .env
load_dotenv()

# Command-line arguments for transport and port
parser = argparse.ArgumentParser(description="Run the MCP GIPHY Server.")
parser.add_argument(
    "--transport",
    default="stdio",
    choices=["stdio", "sse"],
    help="Transport protocol to use ('stdio' or 'sse'). Default is 'stdio'.",
)
parser.add_argument("--port", type=int, default=8000, help="Port to use for SSE (default is 8000).")

# Initialize FastMCP with debug logging.
mcp = FastMCP(name="Giphy MCP Server", log_level="DEBUG")

# Define each tool and its setup.


@mcp.tool()
async def research(context: str, question: str) -> Optional[str]:
    # Perform research using context and question
    return "Researching..."


if __name__ == "__main__":
    args = parser.parse_args()
    if args.transport == "sse":
        mcp.settings.port = args.port

    mcp.run(transport=args.transport)
