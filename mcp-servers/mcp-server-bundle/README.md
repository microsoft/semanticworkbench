# MCP Server Bundle

This project bundles the mcp-filesystem-edit and mcp-tunnel tools into a single executable package for easy distribution and use.

## Features

- Single executable that starts mcp-filesystem-edit and mcp-tunnel
- Graceful shutdown with Ctrl+C (kills all child processes)
- Windows and macOS executable packaging

## Usage

1. Run `make package` to build the executable. It will be output into the `dist` directory.
