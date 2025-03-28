# Main entry point for the MCP Server

import argparse

from . import config
from .server import create_mcp_server


def main() -> None:
    # Command-line arguments for transport and port
    parse_args = argparse.ArgumentParser(description="Start the MCP server.")
    parse_args.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio", "sse"],
        help="Transport protocol to use ('stdio' or 'sse'). Default is 'stdio'.",
    )
    parse_args.add_argument("--port", type=int, default=34737, help="Port to use for SSE (default is 34737).")
    parse_args.add_argument(
        "--enable-client-roots",
        action="store_true",
        default=config.settings.enable_client_roots,
        help="Enable querying of client Roots, which are only supported by some MCP clients.",
    )
    args = parse_args.parse_args()

    config.settings.enable_client_roots = args.enable_client_roots

    mcp = create_mcp_server()
    if args.transport == "sse":
        mcp.settings.port = args.port

    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
