# Main entry point for the MCP Coder Server

import argparse
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables from .env
load_dotenv()

# Command-line arguments for transport and port
parser = argparse.ArgumentParser(description="Run the MCP Coder Server.")
parser.add_argument(
    "--transport",
    default="stdio",
    choices=["stdio", "sse"],
    help="Transport protocol to use ('stdio' or 'sse'). Default is 'stdio'.",
)
parser.add_argument("--port", type=int, default=6010, help="Port to use for SSE (default is 6010).")

# Initialize FastMCP with debug logging.
mcp = FastMCP(name="Coder MCP Server", log_level="DEBUG")

# Define server tool or resource logic here

if __name__ == "__main__":
    args = parser.parse_args()
    if args.transport == "sse":
        mcp.settings.port = args.port

    mcp.run(transport=args.transport)
