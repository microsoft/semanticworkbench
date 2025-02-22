# Copyright (c) Microsoft. All rights reserved.

# Main entry point for the MCP Server

import argparse
from pyngrok import ngrok
from .server import create_mcp_server


def main() -> None:
    # Command-line arguments for transport and port
    parse_args = argparse.ArgumentParser(
        description="Start the MCP server.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parse_args.add_argument(
        "--transport",
        default="sse",
        choices=["stdio", "sse"],
        help="Transport protocol to use ('stdio' or 'sse').",
    )
    parse_args.add_argument("--port", type=int, default=25566, help="Port to use for SSE.")
    parse_args.add_argument(
        "--tunnel",
        action="store_true",
        help="Automatically open an ngrok tunnel to expose the server publicly (only for SSE transport).",
        default=True
    )
    
    args = parse_args.parse_args()

    mcp = create_mcp_server()
    if args.transport == "sse":
        mcp.settings.port = args.port

    if args.tunnel and args.transport == "sse":
        print(f"Starting ngrok tunnel on port {args.port}...")
        tunnel = ngrok.connect(args.port, "http")
        print(f"ngrok tunnel is open: {tunnel.public_url}")
        print("Share this URL with your assistant configuration for remote testing.")

    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
