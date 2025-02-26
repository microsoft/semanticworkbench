"""
Main entry point for MCP Server Bundle.

This module provides the main entry point for the MCP Server Bundle,
which starts the appropriate services based on the platform.
"""

import argparse
import platform
import sys
import time
from typing import Any

from .process_manager import ProcessManager


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


def get_platform_module():
    """
    Get the appropriate platform module based on the current system.

    Returns:
        The platform module for the current system.
    """
    system = platform.system()

    if system == "Windows":
        from .platform import windows

        return windows
    elif system == "Darwin":  # macOS
        from .platform import macos

        return macos
    else:
        print(f"Unsupported platform: {system}")
        sys.exit(1)


def main() -> int:
    """
    Main entry point for the application.

    Returns:
        Exit code.
    """
    manager: ProcessManager | None = None
    try:
        # Parse command-line arguments
        args = parse_arguments()

        # Get the appropriate platform module
        platform_module = get_platform_module()

        # Get the commands to run
        commands = platform_module.get_commands(args)

        if not commands:
            print("No commands to run")
            return 1

        # Create the process manager
        manager = ProcessManager()

        # Set up signal handlers
        manager.setup_signal_handlers()

        # Start each process
        for name, command in commands.items():
            print(f"Starting {name}...")
            if not manager.start_process(name, command):
                print(f"Failed to start {name}")
                manager.terminate_processes()
                return 1

        print("\nAll services started. Press Ctrl+C to exit.\n")

        # Keep the main thread alive and monitor processes
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt. Shutting down...")
        if manager:
            manager.terminate_processes()
        return 0

    except Exception as e:
        print(f"Error: {str(e)}")
        if manager:
            manager.terminate_processes()
        return 1


if __name__ == "__main__":
    sys.exit(main())
