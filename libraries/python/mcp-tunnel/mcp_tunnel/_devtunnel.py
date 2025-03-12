import json
import re
import subprocess
import sys
from typing import Any, Iterable, cast
import uuid

from ._dir import get_mcp_tunnel_dir


def _exec(args: list[str], timeout: float | None = None) -> tuple[int, str, str]:
    """
    Execute a devtunnel command.

    Args:
        args: List of arguments for the devtunnel command.
    Returns:
        A tuple containing:
        - Return code from the command
        - Standard output from the command
        - Standard error from the command
    """
    result = subprocess.run(
        ["devtunnel", *args],
        capture_output=True,
        text=True,
        check=False,  # Don't raise exception if command fails
        timeout=timeout,
    )

    return result.returncode, result.stdout.strip(), result.stderr.strip()


def is_available() -> tuple[bool, str]:
    """
    Check if the devtunnel CLI is available on the system.

    Returns:
        A tuple containing:
        - Boolean indicating if devtunnel is available
        - String with the version information if available, None otherwise
        - Error message if there was a problem with the devtunnel command
    """
    try:
        code, stdout, stderr = _exec(["--version"], timeout=20)

        if code != 0:
            return False, f"devtunnel command returned error code {code}: {stderr}"

        return True, ""

    except FileNotFoundError:
        # Command not found
        return False, "devtunnel command not found in PATH"


def is_logged_in() -> bool:
    """
    Check if the user is logged into the devtunnel CLI.

    Returns:
        Boolean indicating if the user is logged in
    """
    code, stdout, _ = _exec(["user", "show", "--json"], timeout=20)
    if code != 0:
        return False

    # Check the login status from the output
    # the output sometimes includes a welcome message :/
    # so we need to truncate anything prior to the first curly brace
    stdout = stdout[stdout.index("{") :]
    user_response: dict[str, Any] = json.loads(stdout)
    status = (user_response.get("status") or "").lower()
    return  status == "logged in"


def delete_tunnel(tunnel_id: str) -> bool:
    """
    Delete a tunnel by its ID.

    Args:
        tunnel_id: The ID of the tunnel to delete.

    Returns:
        Boolean indicating if the deletion was successful.
    """
    code, _, stderr = _exec(["delete", tunnel_id, "--force"], timeout=20)
    if code == 0:
        return True

    if "not found" in stderr:
        return True

    print("Error deleting tunnel:", stderr, file=sys.stderr)
    return False


def create_tunnel(tunnel_id: str, ports: Iterable[int]) -> tuple[bool, str]:
    """
    Create a tunnel with the given ID and port.

    Args:
        tunnel_id: The ID of the tunnel to create.
        port: The port number for the tunnel.

    Returns:
        Boolean indicating if the creation was successful and the fully qualified tunnel ID.
    """
    code, stdout, stderr = _exec(["create", tunnel_id, "--json"], timeout=20)
    if code != 0:
        print("Error creating tunnel:", stderr, file=sys.stderr)
        return False, ""

    try:
        # the output sometimes includes a welcome message :/
        # so we need to truncate anything prior to the first curly brace
        stdout = stdout[stdout.index("{") :]
        tunnel_response = json.loads(stdout)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error parsing tunnel creation response; response: {stdout}, err: {e}", file=sys.stderr)
        return False, ""

    tunnel: dict[str, Any] = tunnel_response.get("tunnel")
    if not tunnel:
        print("Tunnel creation failed:", tunnel_response, file=sys.stderr)
        return False, ""

    fully_qualified_tunnel_id: str = tunnel.get("tunnelId", "")
    if not fully_qualified_tunnel_id:
        print("Tunnel ID not found in response:", tunnel_response, file=sys.stderr)
        return False, ""

    for port in ports:
        code, _, stderr = _exec(
            ["port", "create", tunnel_id, "--port-number", str(port), "--protocol", "http"], timeout=20
        )
        if code != 0:
            print("Error creating tunnel port:", stderr, file=sys.stderr)
            delete_tunnel(tunnel_id)
            return False, ""

    return True, fully_qualified_tunnel_id


def get_access_token(tunnel_id: str) -> str:
    """
    Get the access token for a tunnel.

    Args:
        tunnel_id: The ID of the tunnel.

    Returns:
        The access token for the tunnel.
    """

    code, stdout, stderr = _exec(["token", tunnel_id, "--scope", "connect", "--json"], timeout=20)
    if code != 0:
        raise RuntimeError(f"Error getting access token: {stderr}")

    # the output sometimes includes a welcome message :/
    # so we need to truncate anything prior to the first curly brace
    stdout = stdout[stdout.index("{") :]
    return json.loads(stdout)["token"]


def get_tunnel_uri(tunnel_id: str, port: int) -> str:
    """
    Get the URI for a tunnel.

    Args:
        tunnel_id: The ID of the tunnel.

    Returns:
        The URI for the tunnel.
    """
    code, stdout, stderr = _exec(["show", tunnel_id, "--json"], timeout=20)
    if code != 0:
        raise RuntimeError(f"Error getting tunnel URI: {stderr}")

    # the output sometimes includes a welcome message :/
    # so we need to truncate anything prior to the first curly brace
    stdout = stdout[stdout.index("{") :]
    tunnel = json.loads(stdout).get("tunnel")
    if not tunnel:
        raise RuntimeError(f"Tunnel {tunnel_id} not found")

    port_infos = cast(list[dict[str, Any]], tunnel.get("ports", []))
    for port_info in port_infos:
        if port_info.get("portNumber") != port:
            continue

        return port_info.get("portUri") or ""

    return ""


def safe_tunnel_id(id: str) -> str:
    """
    Generates a valid devtunnel ID that is guaranteed to be unique for the
    current operating system user and machine.

    Args:
        tunnel_id: The ID of the tunnel.

    Returns:
        The local tunnel ID.
    """

    suffix_path = get_mcp_tunnel_dir() / ".tunnel_suffix"
    suffix = ""

    # read the suffix from the file if it exists
    try:
        suffix = suffix_path.read_text()
    except FileNotFoundError:
        pass

    # if the suffix hasn't been set, generate a new one and cache it in the file
    if not suffix:
        suffix = uuid.uuid4().hex[:10]
        suffix_path.write_text(suffix)

    # dev tunnel ids can only contain lowercase letters, numbers, and hyphens
    tunnel_id = re.sub(r"[^a-z0-9-]", "-", id.lower())

    # dev tunnel ids have a maximum length of 60 characters. we'll keep it to 50, to be safe.
    max_prefix_len = 50 - len(suffix) - 1
    prefix = tunnel_id[:max_prefix_len]

    return f"{prefix}-{suffix}"
