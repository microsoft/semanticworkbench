"""
Main entry point for MCP Server Bundle.

This module provides the main entry point for the MCP Server Bundle,
which starts the appropriate services based on the platform.
"""

import argparse
import os
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from typing import Any

from mcp_tunnel import MCPServer


@dataclass
class MCPServerProcess:
    server: MCPServer
    process: subprocess.Popen | None


MCP_SERVER_OFFICE_PORT = 25252
MCP_SERVER_FILE_SYSTEM_PORT = 59595
MCP_SERVER_VSCODE_PORT = 6010


def parse_arguments() -> dict[str, Any]:
    """
    Parse command-line arguments.

    Returns:
        A dictionary of parsed arguments.
    """
    parser = argparse.ArgumentParser(description="MCP Server Bundle - Packages mcp-server-office and mcp-tunnel")
    args = parser.parse_args()

    return vars(args)


def start_servers() -> list[MCPServerProcess]:
    mcp_servers: list[MCPServerProcess] = []

    for start in [
        start_mcp_server_office,
        start_mcp_server_vscode,
        start_mcp_server_filesystem,
    ]:
        mcp_server = start()
        if mcp_server is not None:
            mcp_servers.append(mcp_server)

    return mcp_servers


def _run_executable(executable_name: str, args: list[str]) -> subprocess.Popen | None:
    is_windows = sys.platform.startswith("win")

    # Get the path to the bundled executable
    # PyInstaller sets _MEIPASS when running from a bundle
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # When running from the PyInstaller bundle
        base_path = sys._MEIPASS  # type: ignore
        executable_path = os.path.join(base_path, "external_executables", executable_name)
        if is_windows:
            executable_path += ".exe"

    else:
        executable_path = f"../{executable_name}/dist/{executable_name}"
        if is_windows:
            executable_path += ".exe"

    if not os.path.exists(executable_path):
        print(f"Executable not found: {executable_path}")
        return None

    return subprocess.Popen([executable_path] + args)


def start_mcp_server_office() -> MCPServerProcess | None:
    process = _run_executable("mcp-server-office", ["--transport", "sse", "--port", str(MCP_SERVER_OFFICE_PORT)])
    if process is None:
        return None

    return MCPServerProcess(MCPServer("mcp-server-office", MCP_SERVER_OFFICE_PORT), process)


def start_mcp_server_vscode() -> MCPServerProcess | None:
    return MCPServerProcess(MCPServer("mcp-server-vscode", MCP_SERVER_VSCODE_PORT), None)


def start_mcp_server_filesystem() -> MCPServerProcess | None:
    process = _run_executable(
        "mcp-server-filesystem", ["--transport", "sse", "--port", str(MCP_SERVER_FILE_SYSTEM_PORT)]
    )
    return MCPServerProcess(
        MCPServer(
            "mcp-server-filesystem",
            MCP_SERVER_FILE_SYSTEM_PORT,
            extras={"roots": ["PUT VALID PATH HERE; ex: file:///c:/dir or file:///Users/me/dir"]},
        ),
        process,
    )


def start_mcp_tunnel(servers: list[MCPServer]) -> None:
    import mcp_tunnel

    threading.Thread(target=mcp_tunnel.tunnel_servers, args=(servers,), daemon=True).start()


def main() -> int:
    """
    Main entry point for the application.

    Returns:
        Exit code.
    """
    mcp_servers_and_processes: list[MCPServerProcess] = []

    try:
        # Parse command-line arguments
        _ = parse_arguments()

        # Start the servers
        mcp_servers_and_processes = start_servers()

        # Start the tunnel
        start_mcp_tunnel([p.server for p in mcp_servers_and_processes])

        print("\nAll services started. Press Ctrl+C to exit.\n")

        # Keep the main thread alive and monitor processes
        while True:
            for server_process in mcp_servers_and_processes:
                if server_process.process is not None:
                    if server_process.process.poll() is not None:
                        print(f"{server_process.server.name} has terminated.")
                        return 1

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt. Shutting down...")

        return 0

    finally:
        for server_process in mcp_servers_and_processes:
            if server_process.process is not None:
                server_process.process.terminate()


if __name__ == "__main__":
    sys.exit(main())
