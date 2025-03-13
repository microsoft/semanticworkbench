import argparse
import json
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
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
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class TunnelledPort:
    tunnel_id: str
    port: int
    sse_url: str
    headers: dict[str, str]
    access_token: str


@dataclass
class MCPTunnel:
    name: str
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
            cprint(f"Warning: Failed to delete existing tunnel", "red", file=sys.stderr)
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
                headers={},
                access_token=access_token,
                tunnel_id=fully_qualified_tunnel_id,
            )
            for port in ports
        ]

        return MCPTunnel(name=fully_qualified_tunnel_id, ports=tunnelled_ports)

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
    extensions_config:
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

    config = {
        "extensions_config": {
            "tools": {
                "enabled": True,
                "personal_mcp_servers": [
                    {
                        "key": server.name,
                        "enabled": True,
                        "command": tunnel.sse_url,
                        "args": [
                            json.dumps({
                                "tunnel_id": tunnel.tunnel_id,
                                "port": tunnel.port,
                                "access_token": tunnel.access_token,
                            })
                        ],
                        "env": [{"key": key, "value": value} for key, value in tunnel.headers.items()],
                        "prompt": "",
                        "long_running": False,
                        "task_completion_estimate": 30,
                        **server.extras,
                    }
                    for server, tunnel in zip(servers, tunnel.ports)
                ],
            }
        }
    }

    config_path = get_mcp_tunnel_dir() / "config.yaml"
    config_path.write_text(yaml.dump(config, sort_keys=False))

    cprint(f"\n{'=' * 80}\n", "green")
    cprint("Assistant config file written:", "green")
    cprint(f"\tDirectory: {config_path.parent}", "green")
    cprint(f"\tFilename: {config_path.name}", "green")
    cprint("\nNext steps:", "green")
    cprint("1. Review the file and replace any placeholder values, if there are any", "green")
    cprint("2. Import the file into an assistant to give it access to the MCP servers", "green")
    cprint(f"\n{'=' * 80}\n", "green")


def tunnel_servers(servers: list[MCPServer]):
    tunnel_manager = TunnelManager(servers)

    # Ensure the `devtunnel` CLI is available
    if not ensure_devtunnel():
        return 1

    print("DevTunnel CLI detected and user is logged in")
    print(f"Starting tunnels for servers: {', '.join(s.name for s in servers)}")

    try:
        # Start all tunnel processes
        tunnels = tunnel_manager.start_tunnel(servers)

        write_assistant_config(servers, tunnels)

        # Keep the main thread alive
        print("All tunnels started. Press Ctrl+C to stop all tunnels.")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt. Shutting down...")
        tunnel_manager.terminate_tunnels()
        return 0

    except Exception as e:
        print(f"Error: {str(e)}")
        tunnel_manager.terminate_tunnels()
        return 1


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
    if not devtunnel.is_logged_in():
        print("Error: You are not logged in to the DevTunnel CLI.", file=sys.stderr)
        print("Please log in using 'devtunnel login' command.", file=sys.stderr)
        return False

    return True


if __name__ == "__main__":
    sys.exit(main())
