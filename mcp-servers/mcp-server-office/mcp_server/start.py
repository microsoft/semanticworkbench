# Copyright (c) Microsoft. All rights reserved.

# Main entry point for the MCP Server

import argparse
import os
from textwrap import dedent

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
    parse_args.add_argument(
        "--use-ngrok-tunnel", action="store_true", help="Use Ngrok tunnel to expose the server to the internet."
    )

    args = parse_args.parse_args()

    use_ngrok = False
    # Warn user of risks and prompt for confirmation before starting Ngrok tunnel
    if args.use_ngrok_tunnel:
        print("\n****************************************************************************************\n")
        print("WARNING: Exposing the server to the internet using Ngrok is a security risk.")
        print("Anyone with the URL can access the server and potentially control your Office apps.")
        print("Ensure you trust the network you are connected to and the devices on it.")
        print("Do not expose the server to the internet unless you understand the risks.\n")
        print(
            dedent("""
            Consider other options like dev tunnels, a free service provided by Microsoft Azure,
            to expose your server to the internet.

            Read more about dev tunnels at:
                - https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started
        """).strip()
        )
        print("\n****************************************************************************************\n")
        if input("Are you sure you want to start Ngrok? (y/N): ").lower() == "y":
            use_ngrok = True
        else:
            print("Ngrok tunnel not started.")

    # Start the Ngrok tunnel if enabled
    if use_ngrok:
        # Prompt for Ngrok auth token if not set
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
                auth_token = input(
                    "Enter your Ngrok auth token (from: https://dashboard.ngrok.com/get-started/your-authtoken): "
                )
                if not auth_token:
                    print("[ERROR] Ngrok auth token is required to start the server.")
                    exit(1)
                # Save the token to the .env file for future use
                with open(env_file, "a") as file:
                    file.write(f"NGROK_AUTHTOKEN={auth_token}\n")
                    print(f"Ngrok auth token saved for future use: {env_file}")
        else:
            print("Loaded Ngrok auth token from environment.")

        # Start Ngrok Tunnel
        print(f"Starting Ngrok tunnel on port {args.port}...")
        try:
            listener = ngrok.forward(args.port, authtoken=auth_token)
            print("\n****************************************************************************************\n")
            print(f"Office MCP Server URL: {listener.url()}/sse\n")
            print("Reminder, this URL exposes the server to the internet. Do not share it with untrusted parties.")
            print("\n****************************************************************************************\n")
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

        if use_ngrok:
            ngrok.kill()


if __name__ == "__main__":
    main()
