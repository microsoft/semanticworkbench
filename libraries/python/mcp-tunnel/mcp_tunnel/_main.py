import argparse
import pathlib
import signal
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from typing import IO, NoReturn, cast

import yaml
from termcolor import cprint
from termcolor._types import Color

from . import _devtunnel as devtunnel


@dataclass
class MCPServer:
    name: str
    port: int


@dataclass
class MCPTunnel:
    name: str
    sse_url: str
    headers: dict[str, str]


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
        suffix = uuid.uuid4().hex[:6]
        self.server_labels = [f"{server.name}-{suffix}" for server in servers]

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

    def start_tunnel(self, server: MCPServer) -> MCPTunnel:
        """Start a single tunnel process for a server."""
        color = cast(Color, self.server_colors[server.name])

        cprint(f"Starting tunnel for {server.name} on port {server.port}...", color)

        if not devtunnel.delete_tunnel(server.name):
            cprint(f"Warning: Failed to delete existing tunnel for {server.name}", color, file=sys.stderr)
            sys.exit(1)

        if not devtunnel.create_tunnel(server.name, server.port):
            cprint(f"Failed to create new tunnel for {server.name}", color, file=sys.stderr)
            sys.exit(1)

        access_token = devtunnel.get_access_token(server.name)

        # Start the devtunnel process
        process = subprocess.Popen(
            ["devtunnel", "host", server.name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
        )

        self.processes[server.name] = process

        # Start threads to read stdout and stderr
        stdout_thread = threading.Thread(
            target=self.output_reader, args=(server.name, process.stdout, color), daemon=True
        )
        stderr_thread = threading.Thread(
            target=self.output_reader, args=(server.name, process.stderr, "red"), daemon=True
        )

        stdout_thread.start()
        stderr_thread.start()

        attempts = 1
        while attempts <= 10:
            time.sleep(1)
            uri = devtunnel.get_tunnel_uri(server.name)

            if not uri:
                attempts += 1
                continue

            cprint(f"Tunnel for {server.name} started successfully: {uri}", color)

            uri = uri.rstrip("/") + "/sse"
            return MCPTunnel(
                name=server.name, sse_url=uri, headers={"X-Tunnel-Authorization": f"tunnel {access_token}"}
            )

        self.terminate_tunnels()
        cprint(f"Failed to start tunnel for {server.name} after 10 attempts", color, file=sys.stderr)
        sys.exit(1)

    def start_all_tunnels(self) -> None:
        """Start all tunnel processes."""

        tunnels: list[MCPTunnel] = []
        for server in self.servers:
            tunnel = self.start_tunnel(server)
            tunnels.append(tunnel)

        self.write_assistant_config(tunnels)

    def write_assistant_config(self, tunnels: list[MCPTunnel]) -> None:
        """
        extensions_config:
        tools:
            enabled: true
            mcp_servers:
            - enabled: true
                key: vscode
                command: https://88c223vw-6010.usw2.devtunnels.ms/sse
                args: []
                env: []
                prompt: ''
                long_running: false
                task_completion_estimate: 30
            - enabled: false
                key: fetch
                command: https://jtsxbnjx-50001.usw2.devtunnels.ms/sse
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
                    "mcp_servers": [
                        {
                            "enabled": True,
                            "key": server.name,
                            "command": tunnel.sse_url,
                            "args": [],
                            "env": [{"key": key, "value": value} for key, value in tunnel.headers.items()],
                            "prompt": "",
                            "long_running": False,
                            "task_completion_estimate": 30,
                        }
                        for server, tunnel in zip(self.servers, tunnels)
                    ],
                }
            }
        }

        mcp_tunnel_dir = pathlib.Path.home() / ".mcp-tunnel"
        mcp_tunnel_dir.mkdir(exist_ok=True)

        config_path = mcp_tunnel_dir / "config.yaml"
        config_path.write_text(yaml.dump(config, sort_keys=False))

        print(f"\nConfig file written to: {config_path}")

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


def parse_servers(servers_str):
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


def main():
    args = parse_arguments()
    servers = parse_servers(args.servers)

    if not servers:
        print("Error: No valid servers specified.")
        return 1

    tunnel_servers(servers)


def tunnel_servers(servers: list[MCPServer]):
    tunnel_manager = TunnelManager(servers)

    # Ensure the `devtunnel` CLI is available
    if not ensure_devtunnel():
        return 1

    print("DevTunnel CLI detected and user is logged in")
    print(f"Starting tunnels for servers: {', '.join(s.name for s in servers)}")

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, tunnel_manager.signal_handler)
    signal.signal(signal.SIGTERM, tunnel_manager.signal_handler)

    try:
        # Start all tunnel processes
        tunnel_manager.start_all_tunnels()

        # Keep the main thread alive
        print("\nAll tunnels started. Press Ctrl+C to stop all tunnels.\n")
        while True:
            time.sleep(1)

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
