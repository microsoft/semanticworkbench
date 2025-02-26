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


def start_threads(args: dict[str, Any]) -> None:
    threading.Thread(target=execute_mcp_server_office, daemon=True).start()
    threading.Thread(target=execute_mcp_tunnel, daemon=True).start()


def execute_mcp_server_office() -> None:
    try:
        if importlib.util.find_spec("mcp_server.start"):
            import mcp_server.start

            mcp_server.start.main()

    except ImportError:
        pass

    print("Warning: mcp-server-office not found")
    return None


def execute_mcp_tunnel() -> list[str]:
    try:
        if importlib.util.find_spec("mcp_tunnel"):
            import mcp_tunnel

            mcp_tunnel.main()
    except ImportError:
        pass

    print("Error: mcp-tunnel not found")
    sys.exit(1)


def main() -> int:
    """
    Main entry point for the application.

    Returns:
        Exit code.
    """
    try:
        # Parse command-line arguments
        args = parse_arguments()

        # Start the threads
        start_threads(args)

        print("\nAll services started. Press Ctrl+C to exit.\n")

        # Keep the main thread alive and monitor processes
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt. Shutting down...")
        return 0


if __name__ == "__main__":
    sys.exit(main())
