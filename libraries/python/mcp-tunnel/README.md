# MCP Tunnel

A command-line tool for managing secure tunnels to local Model Context Protocol (MCP) servers.

## Overview

MCP Tunnel simplifies the process of exposing locally running MCP servers to the internet through secure tunnels. This enables AI assistants like Codespace assistant to connect to your local MCP servers, allowing them to access local resources, files, and functionality.

The tool uses Microsoft's DevTunnel service to create secure tunnels from the internet to your local machine. It can manage multiple tunnels simultaneously and generates the necessary configuration files for connecting your Codespace assistant to these tunnels.

## Prerequisites

- uv
- [Microsoft DevTunnel CLI](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started) installed and available in your PATH
- A Microsoft account (to log in to DevTunnel)

## Quickstart - Run from this repo

Run the mcp-tunnel script directly from this repository using `uvx`:

```bash
uvx --from git+https://github.com/microsoft/semanticworkbench#subdirectory=libraries/python/mcp-tunnel mcp-tunnel --help
```

## Installation for development on a repo clone

After cloning the repo, install MCP Tunnel using make from the `mcp-tunnel` directory:

```bash
make install
```

## Usage

### Basic Usage

Start tunnels for default MCP servers (vscode on port 6010 and office on port 25566):

```bash
uvx --from git+https://github.com/microsoft/semanticworkbench#subdirectory=libraries/python/mcp-tunnel mcp-tunnel
```

or on a cloned repo

```bash
uv run mcp-tunnel
```

### Custom Servers

Specify custom server names and ports:

```bash
uvx --from git+https://github.com/microsoft/semanticworkbench#subdirectory=libraries/python/mcp-tunnel mcp-tunnel --servers "myserver:8080,anotherserver:9000"
```

or on a cloned repo

```bash
uv run mcp-tunnel --servers "myserver:8080,anotherserver:9000"
```

### Output

When you run MCP Tunnel, it will:

1. Check if DevTunnel CLI is installed and you're logged in
2. Create tunnels for each specified server
3. Start tunnel processes and display their output with color-coding
4. Generate a configuration file at `~/.mcp-tunnel/config.yaml`
5. Keep tunnels running until you press Ctrl+C

## Configuration

MCP Tunnel generates a configuration file at `~/.mcp-tunnel/config.yaml` that can be used to connect your AI assistant to the tunnels. The configuration includes:

- SSE endpoints for each tunnel
- Dev tunnel details

You can use this configuration with the Codespace assistant by importing it from the Assistant Configuration screen.

## Troubleshooting

### DevTunnel CLI Not Found

If you see an error about the DevTunnel CLI not being found:

1. Install the DevTunnel CLI by following the [official instructions](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started)
2. Make sure it's in your PATH
3. Test that it works by running `devtunnel --version`

### Not Logged In

If you're not logged in to DevTunnel:

```bash
devtunnel login
```

### Tunnels Not Starting

If tunnels aren't starting, check:

1. That the ports you specified are correct
2. That your local MCP servers are running on those ports
3. That the ports aren't being blocked by a firewall
