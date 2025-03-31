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

1. Check if DevTunnel CLI is installed
2. Check if you are logged in to DevTunnel CLI, and if not, initiate a login
3. Create tunnels for each specified server
4. Start tunnel processes and display their output with color-coding
5. Generate an assistant configuration file at `~/.mcp-tunnel/assistant-config.yaml`, for use with the Codespace assistant
6. Generate an MCP client configuration file at `~/.mcp-tunnel/mcp-client.json`, for use with MCP clients such as Claude desktop
7. Keep tunnels running until you press Ctrl+C

## Assistant Configuration

MCP Tunnel generates a configuration file at `~/.mcp-tunnel/assistant-config.yaml` that can be used to connect your AI assistant to the tunnels.

You can use this configuration with the Codespace assistant by importing it from the Assistant Configuration screen.

## MCP Client Configuration

MCP Tunnel generates a configuration file at `~/.mcp-tunnel/mcp-client.json` that can be used to connect your MCP clients to the tunnels.

Read the documentation for your specific MCP client to learn how to apply this configuration.

### Setting Up Your MCP Client Machine

After running `mcp-tunnel`, you'll need to set up your MCP client machine to connect to the tunnels:

1. **Install DevTunnel**: Follow the [installation instructions](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started?#install)

2. **Log in with your Microsoft account**:

   ```bash
   devtunnel user login
   ```

3. **Start port forwarding** (use the tunnel ID from your `mcp-client.json` output):

   ```bash
   devtunnel connect <TUNNEL_ID>
   ```

4. **Install MCP Proxy**: Follow the [installation instructions](https://github.com/sparfenyuk/mcp-proxy?tab=readme-ov-file#installation)

5. **Update your MCP client configuration** according to the instructions for your specific MCP client

6. **Restart your MCP client** to apply the changes

## Troubleshooting

### DevTunnel CLI Not Found

If you see an error about the DevTunnel CLI not being found:

1. Install the DevTunnel CLI by following the [official instructions](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started)
2. Make sure it's in your PATH
3. Test that it works by running `devtunnel --version`
