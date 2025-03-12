import asyncio
from dataclasses import dataclass
import json
import os
import re
import subprocess
from time import perf_counter
from typing import IO, Any
import logging


logger = logging.getLogger(__name__)


@dataclass
class DevTunnelConfig:
    """Configuration for devtunnel."""

    access_token: str
    tunnel_id: str
    port: int


    def unique_tunnel_id(self) -> str:
        """Generate a unique ID for the tunnel."""
        return f"{self.tunnel_id}-{self.access_token}"


def config_from(args: list[str]) -> DevTunnelConfig | None:
    dev_tunnel_id = ""
    dev_tunnel_access_token = ""
    dev_tunnel_port = 0

    for arg in args:
        try:
            arg_obj = json.loads(arg)
        except json.JSONDecodeError:
            continue

        if not isinstance(arg_obj, dict):
            continue

        dev_tunnel_id: str = arg_obj.get("tunnel_id", "")
        dev_tunnel_access_token = arg_obj.get("access_token", "")
        dev_tunnel_port: int = arg_obj.get("port", 0)
        break

    if not dev_tunnel_id or not dev_tunnel_port:
        return None

    return DevTunnelConfig(
        access_token=dev_tunnel_access_token,
        tunnel_id=dev_tunnel_id,
        port=dev_tunnel_port,
    )


async def forwarded_url_for(devtunnel: DevTunnelConfig, original_url: str) -> str:
    local_port = await _get_devtunnel_local_port(devtunnel)
    return original_url.replace(f":{devtunnel.port}", f":{local_port}", 1)


@dataclass
class DevTunnel:
    """DevTunnel class to manage devtunnel processes."""

    process: subprocess.Popen
    port_mapping: dict[int, int]


_read_lock = asyncio.Lock()
_write_lock = asyncio.Lock()
_dev_tunnels: dict[str, DevTunnel] = {}
_dev_tunnels_retire_at: dict[str, float] = {}
_retirement_task: asyncio.Task | None = None


def _updated_retire_at() -> float:
    return perf_counter() + (60.0 * 60)  # 60 minutes


async def _retire_tunnels() -> None:
    async with _read_lock, _write_lock:
        for tunnel_id, dev_tunnel in list(_dev_tunnels.items()):
            retire_at = _dev_tunnels_retire_at.get(tunnel_id, 0)
            process_is_running = dev_tunnel.process.poll() is None
            should_retire = not process_is_running or perf_counter() >= retire_at

            if not should_retire:
                continue

            _dev_tunnels.pop(tunnel_id, None)
            _dev_tunnels_retire_at.pop(tunnel_id, None)

            if dev_tunnel.process.poll() is not None:
                continue

            # kill processes that are still running
            dev_tunnel.process.kill()

            try:
                dev_tunnel.process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                dev_tunnel.process.terminate()


async def _retire_tunnels_periodically() -> None:
    while True:
        try:
            await _retire_tunnels()
        except Exception:
            logger.exception("error retiring tunnels")

        await asyncio.sleep(60)


async def _get_tunnel(devtunnel: DevTunnelConfig) -> DevTunnel | None:
    async with _read_lock:
        key = devtunnel.unique_tunnel_id()
        dev_tunnel = _dev_tunnels.get(key)

        if not dev_tunnel:
            return None

        # check if the process has exited
        if dev_tunnel.process.poll() is not None:
            return None

        # update the retirement time
        _dev_tunnels_retire_at[key] = _updated_retire_at()
        return dev_tunnel


def _dev_tunnel_command_path() -> str:
    return os.getenv("DEVTUNNEL_COMMAND_PATH", "devtunnel")


async def _create_tunnel(devtunnel: DevTunnelConfig) -> DevTunnel:
    # get details of the tunnel, including ports
    cmd = [
        _dev_tunnel_command_path(),
        "show",
        devtunnel.tunnel_id,
        "--access-token",
        devtunnel.access_token,
        "--json",
    ]
    completed_process = subprocess.run(
        cmd,
        timeout=20,
        text=True,
        capture_output=True,
    )

    if completed_process.returncode != 0:
        raise RuntimeError(
            f"Failed to execute devtunnel show; cmd: {cmd}, exit code: {completed_process.returncode}, error: {completed_process.stderr}"
        )

    try:
        # the output sometimes includes a welcome message :/
        # so we need to truncate anything prior to the first curly brace
        stdout = completed_process.stdout[completed_process.stdout.index("{") :]
        output = json.loads(stdout)
    except (json.JSONDecodeError, ValueError) as e:
        raise RuntimeError(
            f"Failed to parse JSON output from devtunnel show: {e}"
        ) from e

    tunnel: dict[str, Any] = output.get("tunnel")
    if not tunnel:
        raise RuntimeError(f"Tunnel {devtunnel.tunnel_id} not found")

    expected_ports: list[dict] = tunnel.get("ports", [])

    cmd = [
        _dev_tunnel_command_path(),
        "connect",
        devtunnel.tunnel_id,
        "--access-token",
        devtunnel.access_token,
    ]
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,  # line buffered
    )

    if process.stdout is None:
        raise RuntimeError(f"Failed to start devtunnel connect; cmd: {cmd}, exit code: {process.returncode}")

    async def read_port_mapping_from_stdout(
        stdout: IO[str],
    ) -> dict[int, int]:
        # Read the output line by line
        port_mapping = {}
        for line in stdout:
            match = re.search(
                r"Forwarding from 127.0.0.1:(\d+) to host port (\d+).",
                line,
            )
            if match:
                local_port = int(match.group(1))
                host_port = int(match.group(2))
                port_mapping[host_port] = local_port

            if len(port_mapping) == len(expected_ports):
                return port_mapping

        stderr = process.stderr.read() if process.stderr else ""

        raise RuntimeError(f"Failed to read port mapping from devtunnel process; cmd: {cmd}; err: {stderr}")

    async with asyncio.timeout(20):
        port_mapping = await read_port_mapping_from_stdout(process.stdout)

    dev_tunnel = DevTunnel(process=process, port_mapping=port_mapping)

    key = devtunnel.unique_tunnel_id()
    _dev_tunnels[key] = dev_tunnel
    _dev_tunnels_retire_at[key] = _updated_retire_at()

    # start the retirement task if not already started
    global _retirement_task
    if _retirement_task is None:
        _retirement_task = asyncio.create_task(_retire_tunnels_periodically())

    return dev_tunnel


async def _get_devtunnel_local_port(devtunnel: DevTunnelConfig) -> int:
    # try to get tunnel
    dev_tunnel = await _get_tunnel(devtunnel)

    # if not found, lock, and try to get again
    if not dev_tunnel:
        async with _write_lock:
            dev_tunnel = await _get_tunnel(devtunnel)

            # if still not found, create tunnel
            if not dev_tunnel:
                dev_tunnel = await _create_tunnel(devtunnel)

    local_port = dev_tunnel.port_mapping.get(devtunnel.port)
    if local_port is None:
        raise RuntimeError(
            f"Port {devtunnel.port} is not found for tunnel {devtunnel.tunnel_id}. Available ports: {list(dev_tunnel.port_mapping.keys())}"
        )
    return local_port
