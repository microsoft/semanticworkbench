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
    local_port = await _get_devtunnel_local_port(
        tunnel_id=devtunnel.tunnel_id,
        port=devtunnel.port,
        access_token=devtunnel.access_token,
    )
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
    return perf_counter() + (60.0 * 30)  # 30 minutes


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


async def _get_tunnel(tunnel_id: str) -> DevTunnel | None:
    async with _read_lock:
        dev_tunnel = _dev_tunnels.get(tunnel_id)

        if not dev_tunnel:
            return None

        # check if the process has exited
        if dev_tunnel.process.poll() is not None:
            return None

        # update the retirement time
        _dev_tunnels_retire_at[tunnel_id] = _updated_retire_at()
        return dev_tunnel


def _dev_tunnel_command_path() -> str:
    return os.getenv("DEVTUNNEL_COMMAND_PATH", "devtunnel")


async def _create_tunnel(tunnel_id: str, access_token: str) -> DevTunnel:
    # get details of the tunnel, including ports
    completed_process = subprocess.run(
        [
            _dev_tunnel_command_path(),
            "show",
            tunnel_id,
            "--access-token",
            access_token,
            "--json",
        ],
        timeout=20,
        text=True,
        capture_output=True,
    )

    if completed_process.returncode != 0:
        raise RuntimeError(
            f"Failed to execute devtunnel show; exit code: {completed_process.returncode}; error: {completed_process.stderr}"
        )

    try:
        output = json.loads(completed_process.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Failed to parse JSON output from devtunnel show: {e}"
        ) from e

    tunnel: dict[str, Any] = output.get("tunnel")
    if not tunnel:
        raise RuntimeError(f"Tunnel {tunnel_id} not found")

    expected_ports: list[dict] = tunnel.get("ports", [])

    process = subprocess.Popen(
        [
            _dev_tunnel_command_path(),
            "connect",
            tunnel_id,
            "--access-token",
            access_token,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,  # line buffered
    )

    if process.stdout is None:
        raise RuntimeError("Failed to start devtunnel connect")

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

        raise RuntimeError("Failed to read port mapping from devtunnel process")

    async with asyncio.timeout(20):
        port_mapping = await read_port_mapping_from_stdout(process.stdout)

    dev_tunnel = DevTunnel(process=process, port_mapping=port_mapping)
    _dev_tunnels[tunnel_id] = dev_tunnel
    # retire the tunnel after 30 minutes of inactivity
    _dev_tunnels_retire_at[tunnel_id] = _updated_retire_at()

    # start the retirement task if not already started
    global _retirement_task
    if _retirement_task is None:
        _retirement_task = asyncio.create_task(_retire_tunnels_periodically())

    return dev_tunnel


async def _get_devtunnel_local_port(
    tunnel_id: str, port: int, access_token: str
) -> int:
    # try to get tunnel
    dev_tunnel = await _get_tunnel(tunnel_id)

    # if not found, lock, and try to get again
    if not dev_tunnel:
        async with _write_lock:
            dev_tunnel = await _get_tunnel(tunnel_id)

            # if still not found, create tunnel
            if not dev_tunnel:
                dev_tunnel = await _create_tunnel(tunnel_id, access_token)

    local_port = dev_tunnel.port_mapping.get(port)
    if local_port is None:
        raise RuntimeError(
            f"Port {port} is not found for tunnel {tunnel_id}. Available ports: {list(dev_tunnel.port_mapping.keys())}"
        )
    return local_port
