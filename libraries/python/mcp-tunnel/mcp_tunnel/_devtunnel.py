import json
import subprocess
import sys


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
        code, stdout, stderr = _exec(["--version"], timeout=5)

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
    code, stdout, _ = _exec(["user", "show", "--json"], timeout=10)
    if code != 0:
        return False

    # Check the login status from the output
    return json.loads(stdout)["status"] == "Logged in"


def delete_tunnel(tunnel_id: str) -> bool:
    """
    Delete a tunnel by its ID.

    Args:
        tunnel_id: The ID of the tunnel to delete.

    Returns:
        Boolean indicating if the deletion was successful.
    """
    code, _, stderr = _exec(["delete", tunnel_id, "--force"], timeout=10)
    if code == 0:
        return True

    if "not found" in stderr:
        return True

    print("Error deleting tunnel:", stderr, file=sys.stderr)
    return False


def create_tunnel(tunnel_id: str, port: int) -> bool:
    """
    Create a tunnel with the given ID and port.

    Args:
        tunnel_id: The ID of the tunnel to create.
        port: The port number for the tunnel.

    Returns:
        Boolean indicating if the creation was successful.
    """
    code, _, stderr = _exec(["create", tunnel_id], timeout=10)
    if code != 0:
        print("Error creating tunnel:", stderr, file=sys.stderr)
        return False

    code, _, stderr = _exec(["port", "create", tunnel_id, "--port-number", str(port), "--protocol", "http"], timeout=10)
    if code != 0:
        print("Error creating tunnel:", stderr, file=sys.stderr)
        delete_tunnel(tunnel_id)
        return False

    return True


def get_access_token(tunnel_id: str) -> str:
    """
    Get the access token for a tunnel.

    Args:
        tunnel_id: The ID of the tunnel.

    Returns:
        The access token for the tunnel.
    """

    code, stdout, stderr = _exec(["token", tunnel_id, "--scope", "connect", "--json"], timeout=10)
    if code != 0:
        raise RuntimeError(f"Error getting access token: {stderr}")

    return json.loads(stdout)["token"]


def get_tunnel_uri(tunnel_id: str) -> str:
    """
    Get the URI for a tunnel.

    Args:
        tunnel_id: The ID of the tunnel.

    Returns:
        The URI for the tunnel.
    """
    code, stdout, stderr = _exec(["show", tunnel_id, "--json"], timeout=10)
    if code != 0:
        raise RuntimeError(f"Error getting tunnel URI: {stderr}")

    tunnel = json.loads(stdout).get("tunnel")
    if not tunnel:
        raise RuntimeError(f"Tunnel {tunnel_id} not found")

    ports = tunnel.get("ports", [])
    if not ports:
        return ""

    port = ports[0]
    return port.get("portUri") or ""
