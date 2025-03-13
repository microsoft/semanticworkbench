# Copyright (c) Microsoft. All rights reserved.

import argparse

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
    parse_args.add_argument("--port", type=int, default=6030, help="Port to use for SSE (default is 6030).")
    args = parse_args.parse_args()

    mcp = create_mcp_server()
    if args.transport == "sse":
        mcp.settings.port = args.port

    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
