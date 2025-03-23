# Copyright (c) Microsoft. All rights reserved.

import argparse
import logging
import sys

from mcp_server_filesystem_edit import settings
from mcp_server_filesystem_edit.server import create_mcp_server

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
    parse_args.add_argument("--port", type=int, default=25567, help="Port to use for SSE (default is 25567).")
    parse_args.add_argument(
        "--allowed_directories",
        nargs="*",
        help="Space-separated list of directories that the server is allowed to access. Required for stdio transport.",
    )
    parse_args.add_argument(
        "--enable-pdflatex",
        action="store_true",
        help="Enable LaTeX compilation support. Disabled by default.",
    )
    args = parse_args.parse_args()

    # Process allowed directories from command line args
    if args.allowed_directories:
        # settings.allowed_directories = args.allowed_directories
        logger.info(f"Using allowed_directories from command line: {settings.allowed_directories}")

    # Set pdflatex_enabled based on command line argument
    settings.pdflatex_enabled = args.enable_pdflatex
    logger.info(f"LaTeX compilation support: {'enabled' if settings.pdflatex_enabled else 'disabled'}")

    mcp = create_mcp_server()

    if args.transport == "sse":
        mcp.settings.port = args.port
        # For SSE, the directories are provided directly as query parameters
        logger.info(f"Starting SSE server on port {args.port}")

    else:
        # For stdio, directories must be provided via command line
        if not settings.allowed_directories:
            logger.error("At least one allowed_directory must be specified for stdio transport")
            sys.exit(1)

        logger.info("Starting with stdio transport")
        logger.info(f"Using allowed_directories: {settings.allowed_directories}")

    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
