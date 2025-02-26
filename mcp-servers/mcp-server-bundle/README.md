# MCP Server Bundle

This project bundles the mcp-server-office and mcp-tunnel tools into a single executable package for easy distribution and use.

## Features

- Single executable that starts both mcp-server-office and mcp-tunnel
- Graceful shutdown with Ctrl+C (kills all child processes)
- Windows (.exe) and macOS (.dmg/.pkg) packaging
- macOS version includes only mcp-tunnel (no mcp-server-office)
