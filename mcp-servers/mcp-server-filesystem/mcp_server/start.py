# Main entry point for the MCP Server

import argparse
import sys
import logging

from . import settings
from .server import create_mcp_server

# Set up logging
logger = logging.getLogger("mcp_server_filesystem")

def main() -> None:
    # Command-line arguments for transport and port
    parse_args = argparse.ArgumentParser(description="Start the MCP server.")
    parse_args.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio", "sse"],
        help="Transport protocol to use ('stdio' or 'sse'). Default is 'stdio'.",
    )
    parse_args.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to use for SSE (default is 8000)."
    )
    parse_args.add_argument(
        "--allowed_directories",
        nargs="*",
        help="Space-separated list of directories that the server is allowed to access. Required for stdio transport."
    )
    args = parse_args.parse_args()

    # Process allowed directories from command line args
    if args.allowed_directories:
        settings.allowed_directories = args.allowed_directories
        logger.info(f"Using allowed_directories from command line: {settings.allowed_directories}")

    # Create the server
    mcp = create_mcp_server()

    if args.transport == "sse":
        # For SSE, the directories are provided directly as query parameters
        mcp.settings.port = args.port
        logger.info(f"Starting SSE server on port {args.port}")
        # Note: The client will add all args as a comma-separated list in the 'args' parameter
        logger.info(f"Example usage: Use http://127.0.0.1:{args.port}/sse?args=/path1,/path2,/path3 or configure with args=['/path1', '/path2', '/path3']")
        
        # Setting port in MCP settings
        mcp.settings.port = args.port
    else:  # stdio transport
        # For stdio, directories must be provided via command line
        if not settings.allowed_directories:
            logger.error("At least one allowed_directory must be specified for stdio transport")
            sys.exit(1)
        logger.info(f"Starting with stdio transport")
        logger.info(f"Using allowed_directories: {settings.allowed_directories}")

    # Run with the selected transport
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
