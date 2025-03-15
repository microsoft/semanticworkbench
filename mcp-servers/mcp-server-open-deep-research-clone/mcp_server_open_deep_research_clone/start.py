# Main entry point for the MCP Server

import argparse

from .server import create_mcp_server
from .config import ensure_required_settings


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
        "--port", type=int, default=45567, help="Port to use for SSE (default is 45567)."
    )
    args = parse_args.parse_args()

    mcp = create_mcp_server()
    if args.transport == "sse":
        mcp.settings.port = args.port

    ensure_required_settings()

    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
