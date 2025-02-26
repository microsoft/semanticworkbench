# MCP Server Bundle

This project bundles the mcp-server-office, mcp-server-filesystem, and mcp-tunnel tools into a single executable package for easy distribution and use.

## Features

- Single executable that starts mcp-server-office, mcp-server-filesystem, and mcp-tunnel
- Graceful shutdown with Ctrl+C (kills all child processes)
- Windows and macOS executable packaging
- macOS version includes only mcp-tunnel and mcp-server-filesystem (no mcp-server-office)
