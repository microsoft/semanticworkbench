import argparse
import json
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, Any, NoReturn

import yaml
from termcolor import cprint
from termcolor._types import Color

from . import _devtunnel as devtunnel
from ._dir import get_mcp_tunnel_dir


@dataclass
class MCPServer:
    name: str
    port: int
    extra_assistant_config: dict[str, Any] = field(default_factory=dict)


@dataclass
class TunnelledPort:
    tunnel_id: str
    port: int
    sse_url: str


@dataclass
class MCPTunnel:
    tunnel_id: str
    access_token: str
    ports: list[TunnelledPort]


class TunnelManager:
    def __init__(self, servers: list[MCPServer]):
        self.servers = servers
        self.processes: dict[str, subprocess.Popen] = {}
        self.should_terminate = threading.Event()
        self.server_colors = {
            servers[i].name: [
                "cyan",
                "magenta",
                "green",
                "yellow",
                "blue",
                "white",
                "light_grey",
            ][i % 7]
            for i in range(len(servers))
        }

    def output_reader(self, server_name: str, stream: IO, color: Color):
        """Thread function to read output from a process stream and print it."""

        prefix = f"[{server_name}] "

        while not self.should_terminate.is_set():
            line = stream.readline()
            if not line:
                break

            line_text = line.rstrip()
            cprint(f"{prefix}{line_text}", color)

        # Make sure we read any remaining output after termination signal
        remaining_lines = list(stream)
        for line in remaining_lines:
            line_text = line.rstrip()
            cprint(f"{prefix}{line_text}", color)

    def start_tunnel(self, servers: list[MCPServer]) -> MCPTunnel:
        """Start a single tunnel process for a server."""

        ports = [server.port for server in servers]

        color = "yellow"
        tunnel_id = devtunnel.safe_tunnel_id("/".join((f"{server.name}-{server.port}" for server in servers)))

        cprint(f"Starting tunnel for ports {ports}...", color)

        if not devtunnel.delete_tunnel(tunnel_id):
            cprint("Warning: Failed to delete existing tunnel", "red", file=sys.stderr)
            sys.exit(1)

        success, fully_qualified_tunnel_id = devtunnel.create_tunnel(tunnel_id, ports)
        if not success:
            cprint(f"Failed to create new tunnel for ports {ports}", "red", file=sys.stderr)
            sys.exit(1)

        access_token = devtunnel.get_access_token(tunnel_id)

        # Start the devtunnel process
        process = subprocess.Popen(
            ["devtunnel", "host", tunnel_id],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
        )

        self.processes[tunnel_id] = process

        # Start threads to read stdout and stderr
        stdout_thread = threading.Thread(
            target=self.output_reader, args=(tunnel_id, process.stdout, color), daemon=True
        )
        stderr_thread = threading.Thread(
            target=self.output_reader, args=(tunnel_id, process.stderr, "red"), daemon=True
        )

        stdout_thread.start()
        stderr_thread.start()

        tunnelled_ports = [
            TunnelledPort(
                port=port,
                sse_url=f"http://127.0.0.1:{port}/sse",
                tunnel_id=fully_qualified_tunnel_id,
            )
            for port in ports
        ]

        return MCPTunnel(tunnel_id=fully_qualified_tunnel_id, ports=tunnelled_ports, access_token=access_token)

    def terminate_tunnels(self) -> None:
        """Terminate all running tunnel processes."""
        if not self.processes:
            return

        print("\nShutting down all tunnels...")
        self.should_terminate.set()

        # First send SIGTERM to all processes
        for name, process in self.processes.items():
            print(f"Terminating {name} tunnel...")
            process.terminate()

        # Wait for processes to terminate gracefully
        for _ in range(5):  # Wait up to 5 seconds
            if all(process.poll() is not None for process in self.processes.values()):
                break
            time.sleep(1)

        # Force kill any remaining processes
        for name, process in list(self.processes.items()):
            if process.poll() is None:
                print(f"Force killing {name} tunnel...")
                process.kill()
                process.wait()

        self.processes.clear()
        print("All tunnels shut down.")

    def signal_handler(self, sig, frame) -> NoReturn:
        """Handle Ctrl+C and other termination signals."""
        print("\nReceived termination signal. Shutting down...")
        self.terminate_tunnels()
        sys.exit(0)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run multiple devtunnel processes in parallel")
    parser.add_argument(
        "--servers",
        type=str,
        default="vscode:6010,office:25566",
        help="Comma-separated list of server_name:port pairs (default: vscode:6010,office:25566)",
    )
    return parser.parse_args()


def parse_servers(servers_str: str) -> list[MCPServer]:
    """Parse the servers string into a list of MCPServer objects."""
    servers = []
    for server_str in servers_str.split(","):
        if ":" not in server_str:
            print(f"Warning: Invalid server format: {server_str}. Expected format: name:port")
            continue

        name, port_str = server_str.split(":", 1)
        try:
            port = int(port_str)
            servers.append(MCPServer(name, port))
        except ValueError:
            print(f"Warning: Invalid port number: {port_str} for server {name}")

    return servers


def main() -> int:
    args = parse_arguments()
    servers = parse_servers(args.servers)

    if not servers:
        print("Error: No valid servers specified.")
        return 1

    tunnel_servers(servers)

    return 0


def write_assistant_config(servers: list[MCPServer], tunnel: MCPTunnel) -> None:
    """
    tools:
        enabled: true
        personal_mcp_servers:
        - enabled: true
            key: vscode
            command: https://aaaaa-6010.usw2.devtunnels.ms/sse
            args: []
            env: []
            prompt: ''
            long_running: false
            task_completion_estimate: 30
        - enabled: false
            key: fetch
            command: https://aaaaa-50001.usw2.devtunnels.ms/sse
            args: []
            env: []
            prompt: ''
            long_running: false
            task_completion_estimate: 30
    """

    personal_mcp_servers = []
    for server, port in zip(servers, tunnel.ports):
        server_config = {
            "key": server.name,
            "enabled": True,
            "command": port.sse_url,
            "args": [
                json.dumps({
                    "tunnel_id": port.tunnel_id,
                    "port": port.port,
                    "access_token": tunnel.access_token,
                })
            ],
            "prompt": "",
            "long_running": False,
            "task_completion_estimate": 30,
            **server.extra_assistant_config,
        }

        # Special handling for the filesystem-edit server
        if server.name == "mcp-server-filesystem-edit" and sys.platform.startswith("win32"):
            temp_root = Path("C:/ProgramData/SemanticWorkbench/OfficeWorkingDirectory")
            server_config["roots"] = [{"name": "working_directory", "uri": str(temp_root)}]
            cprint(f"Configured filesystem-edit root directory: {temp_root}", "cyan")

        personal_mcp_servers.append(server_config)

    config = {"tools": {"enabled": True, "personal_mcp_servers": personal_mcp_servers}}

    config_path = get_mcp_tunnel_dir() / "assistant-config.yaml"
    config_path.write_text(yaml.dump(config, sort_keys=False))

    cprint("\n\nAssistant config", "green")
    cprint(f"{'-' * 80}\n", "green")
    cprint(f"\tDirectory: {config_path.parent}", "green")
    cprint(f"\tFile: {config_path}", "green")
    cprint("\nNext steps:", "green")
    cprint("1. Review the file and replace any placeholder values, if there are any", "green")
    cprint("2. Import the file into an assistant to give it access to the MCP servers", "green")


def write_mcp_client_config(servers: list[MCPServer], tunnel: MCPTunnel) -> None:
    """Write MCP client configuration file (mcp-client.json) for use with MCP clients."""

    # Generate mcp-client.json
    mcp_client_config = {
        "mcpServers": {
            server.name: {
                "command": "mcp-proxy",
                "args": [
                    port.sse_url,
                ],
            }
            for server, port in zip(servers, tunnel.ports)
        }
    }

    # Write mcp-client.json
    mcp_client_path = get_mcp_tunnel_dir() / "mcp-client.json"
    mcp_client_path.write_text(json.dumps(mcp_client_config, indent=2))

    cprint("\n\nMCP client config", "green")
    cprint(f"{'-' * 80}\n", "green")
    cprint(f"\tDirectory: {mcp_client_path.parent}", "green")
    cprint(f"\tFile: {mcp_client_path}", "green")
    cprint("\nNext steps:", "green")
    cprint("1. Review the file and replace any placeholder values, if there are any", "green")
    cprint("\nOn your MCP client machine:", "green")
    cprint(
        "1. Install devtunnel https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started?#install",
        "green",
    )
    cprint("2. Login with the same Microsoft account:", "green")
    cprint("        devtunnel user login")
    cprint("3. Start port forwarding:", "green")
    cprint(f"        devtunnel connect {tunnel.tunnel_id}")
    cprint("4. Install mcp-proxy https://github.com/sparfenyuk/mcp-proxy?tab=readme-ov-file#installation", "green")
    cprint("5. Update your MCP client config according to the instructions for your MCP client", "green")
    cprint("6. Restart your MCP client", "green")


def tunnel_servers(servers: list[MCPServer]) -> None:
    tunnel_manager = TunnelManager(servers)

    # Ensure the `devtunnel` CLI is available
    if not ensure_devtunnel():
        sys.exit(1)

    print("User is logged in to devtunnel")
    print(f"Starting tunnels for servers: {', '.join(s.name for s in servers)}")

    try:
        # Start all tunnel processes
        tunnels = tunnel_manager.start_tunnel(servers)

        cprint(f"\n{'=' * 80}", "green")
        write_assistant_config(servers, tunnels)
        write_mcp_client_config(servers, tunnels)
        cprint(f"\n\n{'=' * 80}\n", "green")

        # Keep the main thread alive
        print("All tunnels started. Press Ctrl+C to stop all tunnels.")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt. Shutting down...")
        tunnel_manager.terminate_tunnels()
        return

    except Exception as e:
        print(f"Error: {str(e)}")
        tunnel_manager.terminate_tunnels()
        sys.exit(1)


def ensure_devtunnel() -> bool:
    # Ensure the `devtunnel` CLI is available
    devtunnel_available, error_msg = devtunnel.is_available()
    if not devtunnel_available:
        print("Error: The 'devtunnel' CLI is not available or not working properly.", file=sys.stderr)
        if error_msg:
            print(f"Details: {error_msg}", file=sys.stderr)
        print("Please install the DevTunnel CLI to use this tool.", file=sys.stderr)
        print(
            "For installation instructions, visit: https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started",
            file=sys.stderr,
        )
        return False

    # Ensure the user is logged in to the `devtunnel` CLI
    logged_in = devtunnel.is_logged_in()

    if not logged_in:
        logged_in = devtunnel.login()

    if not logged_in:
        print("Error: DevTunnel login failed.", file=sys.stderr)
        return False

    return True


if __name__ == "__main__":
    sys.exit(main())
