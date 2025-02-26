"""
Main entry point for MCP Server Bundle.

This module provides the main entry point for the MCP Server Bundle,
which starts the appropriate services based on the platform.
"""

import argparse
import importlib.util
import platform
import sys
import threading
import time
from typing import Any
from unittest.mock import patch

from mcp_tunnel import MCPServer


def parse_arguments() -> dict[str, Any]:
    """
    Parse command-line arguments.

    Returns:
        A dictionary of parsed arguments.
    """
    parser = argparse.ArgumentParser(description="MCP Server Bundle - Packages mcp-server-office and mcp-tunnel")

    # Common arguments
    parser.add_argument("--tunnel", nargs="+", help="Additional arguments to pass to mcp-tunnel")

    # Windows-specific arguments
    if platform.system() == "Windows":
        parser.add_argument("--office", nargs="+", help="Additional arguments to pass to mcp-server-office")

    args = parser.parse_args()
    return vars(args)


def start_servers(args: dict[str, Any]) -> list[MCPServer]:
    mcp_servers: list[MCPServer] = []

    for start in [start_mcp_server_office, start_mcp_server_vscode, start_mcp_server_filesystem]:
        mcp_server = start()
        if mcp_server is not None:
            mcp_servers.append(mcp_server)

    return mcp_servers


MCP_SERVER_OFFICE_PORT = 25252


def start_mcp_server_office() -> MCPServer | None:
    try:
        if importlib.util.find_spec("mcp_server.start"):
            threading.Thread(target=_execute_mcp_server_office, daemon=True).start()

            return MCPServer("mcp-server-office", MCP_SERVER_OFFICE_PORT)

    except ImportError:
        pass

    return None


def _execute_mcp_server_office() -> None:
    import mcp_server.start

    with patch.object(sys, "argv", ["mcp-server-office", "--transport", "sse", "--port", str(MCP_SERVER_OFFICE_PORT)]):
        mcp_server.start.main()


def start_mcp_server_vscode() -> MCPServer | None:
    return MCPServer("mcp-server-vscode", 6010)


MCP_SERVER_FILE_SYSTEM_PORT = 59595


def start_mcp_server_filesystem() -> MCPServer | None:
    try:
        if importlib.util.find_spec("mcp_server_filesystem.start"):
            threading.Thread(target=_execute_mcp_server_filesystem, daemon=True).start()
            return MCPServer("mcp-server-filesystem", MCP_SERVER_FILE_SYSTEM_PORT)

    except ImportError:
        pass

    return None


def _execute_mcp_server_filesystem() -> None:
    import mcp_server_filesystem.start

    with patch.object(
        sys, "argv", ["mcp-server-filesystem", "--port", str(MCP_SERVER_FILE_SYSTEM_PORT), "--transport", "sse"]
    ):
        mcp_server_filesystem.start.main()


def start_mcp_tunnel(servers: list[MCPServer]) -> None:
    import mcp_tunnel

    threading.Thread(target=mcp_tunnel.tunnel_servers, args=(servers,), daemon=True).start()


def main() -> int:
    """
    Main entry point for the application.

    Returns:
        Exit code.
    """
    try:
        # Parse command-line arguments
        args = parse_arguments()

        # Start the servers
        mcp_servers = start_servers(args)

        # Start the tunnel
        start_mcp_tunnel(mcp_servers)

        print("\nAll services started. Press Ctrl+C to exit.\n")

        # Keep the main thread alive and monitor processes
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt. Shutting down...")
        return 0


if __name__ == "__main__":
    sys.exit(main())
