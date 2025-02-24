## How to connect the Codespace Assistant (hosted at semantic-workbench.azurewebsites.net) to local MCP servers

NOTE: If you are running the workbench and the assistant locally, this guide will NOT help you.

To connect assistants running in the hosted workbench to a local MCP server, the MCP server needs to be available as an SSE service connectable from the public internet.
To make it accessible, you need to set up a tunnel to the localhost server.
We recommend using the Azure devtunnel service, as it provides a simple and reliable way to create a tunnel.
For MCP servers that only support stdio transport, you additionally need to run `mcp-proxy`, to expose the app as an HTTP/SSE service.

## Standard input/output (stdio) transport

If the MCP server supports SSE transport, you can skip this step.

For MCP servers that only support stdio transport, you can use the mcp-proxy to expose the app as an HTTP/SSE service.

### Step 1: Determine the command to run the MCP server

This will be in the docs for the MCP server you are using.

### Step 2: Run mcp-proxy

Pick an unused port (e.g. 50001) and run the following command:

```bash
# Option 1: With uv (recommended)
uvx mcp-proxy --sse-port={port} {command}

# Option 2: With pipx (alternative)
pipx run mcp-proxy --sse-port={port} {command}
```

Example for port 50001 and command `uvx mcp-server-fetch`:

```bash
uvx mcp-proxy --sse-port=50001 uvx mcp-server-fetch
```

## HTTP Server-Sent Events (SSE) transport

For MCP servers that support HTTP/SSE transport, or servers for which you have set up the proxy, you can use the Azure devtunnel service to create a tunnel to the localhost server.

### Step 1: Install [devtunnel CLI](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started#install)

```bash
# Windows
winget install Microsoft.DevTunnel

# Mac
brew install --cask devtunnel

#Linux
curl -sL https://aka.ms/DevTunnelCliInstall | bash
```

### Step 2: Log in to devtunnel

```bash
devtunnel user login
```

### Step 3: Determine which port the MCP server is running on

The default port that an MCP server runs on will be in the docs for the MCP server you are using. This port will often be configurable.

For servers that you have set up the proxy for, the port is the one you specified in the `--sse-port` argument when running `mcp-proxy`.

### Step 4: Create a tunnel

```bash
devtunnel host -p {mcp-server-port} --allow-anonymous --protocol http
```

Example for MCP server running on port 50001:

```bash
devtunnel host -p 50001 --allow-anonymous --protocol http
```

### Step 4: Copy the tunnel URL

`devtunnel` will print a URL like this:

```
Connect via browser: https://...
```

NOTE: Make sure you copy the "Connect via browser" URL, not the "Inspect network activity" URL.

## Configure the Codespace Assistant

1. Open the [semantic-workbench](https://semantic-workbench.azurewebsites.net) in your browser.
1. Create a conversation with a Codespace Assistant or open an existing one.
1. Click the "Conversation canvas" button in the top-right corner, near your profile picture.
1. Click the "..." button next to the assistant, and click "Configure".
1. Scroll down to the "MCP Servers" section.
1. Delete the default MCP servers using the "Delete" button, if there are any. (They aren't accessible from the workbench and will cause errors.)
1. Click the "+ Add" button.
1. Update the "Key" field to give it a relevant name (e.g. "vscode" or "word").
1. Update the "Command" field to the tunnel URL you copied in the previous step, plus `/sse`. For example, if your tunnel URL is `https://abcdefghi123.usw2.devtunnels.ms`, the command should be `https://c2z6r7s8-6010.usw2.devtunnels.ms/sse`.
1. Click "Save".
1. Click "Close".
1. As a test, try asking the assistant "what tools do you have?".
