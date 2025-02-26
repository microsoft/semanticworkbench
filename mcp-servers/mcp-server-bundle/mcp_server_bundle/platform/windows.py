"""
Windows-specific implementation for MCP Server Bundle.

This module provides Windows-specific functionality for finding and configuring
mcp-server-office and mcp-tunnel commands.
"""

import shutil
import sys
import importlib.util
from typing import Any


def get_commands(args: dict[str, Any]) -> dict[str, list[str]]:
    """
    Get the commands to run for Windows.

    Args:
        args: Command-line arguments.

    Returns:
        A dictionary mapping service names to command lists.
    """
    commands = {}

    # Get mcp-server-office command
    office_command = get_mcp_server_office_command()
    if office_command:
        # Add any additional arguments
        if args.get("office"):
            office_command.extend(args["office"])

        commands["office"] = office_command

    # Get mcp-tunnel command
    tunnel_command = get_mcp_tunnel_command()

    # Add any additional arguments
    if args.get("tunnel"):
        tunnel_command.extend(args["tunnel"])

    commands["tunnel"] = tunnel_command

    return commands


def get_mcp_server_office_command() -> list[str] | None:
    """
    Get the command to run mcp-server-office.

    Returns:
        A list of strings representing the command, or None if not found.
    """
    # Try to find mcp-server-office.exe in PATH
    mcp_server_office_path = shutil.which("mcp-server-office")
    if mcp_server_office_path:
        return [mcp_server_office_path]

    # Try to find mcp-server-office module
    try:
        if importlib.util.find_spec("mcp_server"):
            return ["python", "-m", "mcp_server.start"]
    except ImportError:
        pass

    print("Warning: mcp-server-office not found")
    return None


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
            return ["python", "-m", "mcp_tunnel"]
    except ImportError:
        pass

    # Fallback to mcp_stdio
    try:
        if importlib.util.find_spec("mcp_stdio"):
            return ["python", "-m", "mcp_stdio"]
    except ImportError:
        pass

    print("Error: mcp-tunnel not found")
    sys.exit(1)
