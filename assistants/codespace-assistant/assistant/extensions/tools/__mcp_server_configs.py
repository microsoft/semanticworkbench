from typing import List

from .__model import MCPServerConfig

# List of MCP server configurations
# Each configuration includes the server name, command, arguments, and environment variables.
# Tested with 'npx' commands and _should_ work with 'uvx' as well.
# Can also use 'node' (and probably 'python'), but requires the full path to the lib/script called.

mcp_server_configs: List[MCPServerConfig] = [
    MCPServerConfig(
        name="Filesystem MCP Server",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/workspaces/semanticworkbench"],
    ),
    MCPServerConfig(
        name="Web Research MCP Server",
        command="npx",
        args=["-y", "@mzxrai/mcp-webresearch@latest"],
    ),
]
