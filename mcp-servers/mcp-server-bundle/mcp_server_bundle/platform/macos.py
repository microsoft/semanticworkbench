"""
macOS-specific implementation for MCP Server Bundle.

This module provides macOS-specific functionality for finding and configuring
mcp-tunnel commands. Note that mcp-server-office is not supported on macOS.
"""

import importlib.util
import shutil
import sys
from typing import Any


def get_commands(args: dict[str, Any]) -> dict[str, list[str]]:
    """
    Get the commands to run for macOS.

    Args:
        args: Command-line arguments.

    Returns:
        A dictionary mapping service names to command lists.
    """
    commands = {}

    # Get mcp-tunnel command
    tunnel_command = get_mcp_tunnel_command()

    # Add any additional arguments
    if args.get("tunnel"):
        tunnel_command.extend(args["tunnel"])

    commands["tunnel"] = tunnel_command

    return commands


def get_mcp_tunnel_command() -> list[str]:
    """
    Get the command to run mcp-tunnel.

    Returns:
        A list of strings representing the command.
    """
    # Try to find mcp-tunnel in PATH
    mcp_tunnel_path = shutil.which("mcp-tunnel")
    if mcp_tunnel_path:
        return [mcp_tunnel_path]

    # Try to find mcp_tunnel module
    try:
        if importlib.util.find_spec("mcp_tunnel"):
            return ["python3", "-m", "mcp_tunnel"]
    except ImportError:
        pass

    print("Error: mcp-tunnel not found")
    sys.exit(1)
