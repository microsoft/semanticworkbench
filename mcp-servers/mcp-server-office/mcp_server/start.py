# Copyright (c) Microsoft. All rights reserved.

# Main entry point for the MCP Server

import argparse
import os

import ngrok

from mcp_server.server import create_mcp_server


def main() -> None:
    # Command-line arguments for transport and port
    parse_args = argparse.ArgumentParser(
        description="Start the MCP server.", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parse_args.add_argument(
        "--transport",
        default="sse",
        choices=["stdio", "sse"],
        help="Transport protocol to use ('stdio' or 'sse').",
    )
    parse_args.add_argument("--port", type=int, default=25566, help="Port to use for SSE.")

    args = parse_args.parse_args()

    # Prompt for Ngrok Auth Token if not set
    auth_token = os.getenv("NGROK_AUTHTOKEN")
    # Check if token is stored in a .env file
    env_file = ".env"
    if not auth_token:
        if os.path.exists(env_file):
            with open(env_file, "r") as file:
                for line in file:
                    if line.startswith("NGROK_AUTHTOKEN"):
                        auth_token = line.split("=", 1)[1].strip()
                        break
        if not auth_token:
            auth_token = input("Enter your Ngrok Auth Token: ")
            if not auth_token:
                print("[ERROR] Ngrok Auth Token is required to start the server.")
                exit(1)
            # Save the token to the .env file for future use
            with open(env_file, "a") as file:
                file.write(f"NGROK_AUTHTOKEN={auth_token}\n")
                print(f"Ngrok Auth Token saved to: {env_file}")
    else:
        print("Using Ngrok Auth Token from environment.")

    # ngrok.set_auth_token(auth_token)

    # Start Ngrok Tunnel
    print(f"Starting Ngrok tunnel on port {args.port}...")
    try:
        listener = ngrok.forward(args.port, authtoken=auth_token)
        print(f"\nOffice MCP Server URL: {listener.url()}/sse\n")
    except Exception as e:
        print(f"[ERROR] Failed to start Ngrok tunnel: {str(e)}")
        exit(1)

    mcp = create_mcp_server()
    if args.transport == "sse":
        mcp.settings.port = args.port

    try:
        mcp.run(transport=args.transport)
    except KeyboardInterrupt:
        print("Shutting down server...")
        ngrok.kill()


if __name__ == "__main__":
    main()
