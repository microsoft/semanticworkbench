from pathlib import Path


def get_mcp_tunnel_dir() -> Path:
    mcp_tunnel_dir = Path.home() / ".mcp-tunnel"
    mcp_tunnel_dir.mkdir(exist_ok=True)
    return mcp_tunnel_dir
