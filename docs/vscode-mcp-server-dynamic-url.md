# VSCode MCP Server Dynamic URL

This document explains how the VSCode MCP server URL is dynamically pulled from the VSCode output for the semantic workbench.

## Overview

The VSCode MCP server extension provides tools and resources from VSCode as a Model Context Protocol (MCP) server. When the server starts, it listens on a specific port (default: 6010) and exposes an SSE endpoint at `http://127.0.0.1:{port}/sse`.

Previously, this URL was hardcoded in the assistant configuration files. Now, the URL is dynamically pulled from the VSCode output, ensuring that the semantic workbench always uses the correct URL, even if the port changes.

## How It Works

The dynamic URL feature works at multiple levels:

1. **VSCode MCP Server Extension**:
   - When the server starts, it stores the URL in a global variable (`__VSCODE_MCP_SERVER_URL`)
   - It runs a script to update all assistant configuration files with the current URL
   - When the server stops, it clears the global variable and updates the configuration files

2. **Semantic Workbench Integration**:
   - Utility functions in the semantic workbench access the global variable to get the current URL
   - The configuration handling code uses these functions to ensure the dynamic URL is used

3. **Configuration File Updates**:
   - A Node.js script (`scripts/update-vscode-mcp-url.js`) finds and updates all assistant configuration files
   - The script is run automatically when the VSCode MCP server starts or stops
   - It can also be run manually to update the configuration files

## Using the Dynamic URL

As a user, you don't need to do anything special to use the dynamic URL feature. It works automatically in the background.

If you're developing with the semantic workbench and VSCode MCP server, here are some things to know:

### Changing the VSCode MCP Server Port

If you need to change the port that the VSCode MCP server listens on:

1. Use the Command Palette (Ctrl+Shift+P)
2. Search for "MCP Server: Set Port"
3. Enter a new port number
4. The server will restart with the new port, and the URL will be automatically updated

### Manually Updating Configuration Files

If you need to manually update the assistant configuration files:

```bash
node /workspaces/semanticworkbench/scripts/update-vscode-mcp-url.js
```

This script will:
- Find all assistant configuration files
- Check if the VSCode MCP server is running
- Update the configuration files with the current URL

### Accessing the Dynamic URL in Code

If you need to access the dynamic URL in your code:

```typescript
import { getVSCodeMcpServerUrl } from './services/workbench';

// Get the dynamic URL
const url = getVSCodeMcpServerUrl();

// Get the dynamic URL with a fallback
const urlWithFallback = getVSCodeMcpServerUrlWithFallback('http://127.0.0.1:6010/sse');
```

## Technical Details

### Global Variable

The VSCode MCP server extension sets a global variable when the server starts:

```typescript
global.__VSCODE_MCP_SERVER_URL = `http://127.0.0.1:${port}/sse`;
```

This variable is accessible to other Node.js processes running in the same context.

### Utility Functions

The semantic workbench includes utility functions to access and update the dynamic URL:

- `getVSCodeMcpServerUrl()`: Gets the URL from the global variable
- `getVSCodeMcpServerUrlWithFallback(defaultUrl)`: Gets the URL with a fallback
- `updateVSCodeMcpServerUrl(config)`: Updates the URL in a configuration object

### Update Script

The update script (`scripts/update-vscode-mcp-url.js`) is a Node.js script that:

1. Checks if the VSCode MCP server is running
2. Finds all assistant configuration files
3. Updates the configuration files with the current URL

The script is run automatically when the VSCode MCP server starts or stops, and can also be run manually.

## Troubleshooting

If you encounter issues with the dynamic URL feature:

1. **Check if the VSCode MCP server is running**:
   - Use the Command Palette to check the status
   - Or run `ps aux | grep mcp-server-vscode` to see if the process is running

2. **Check the configuration files**:
   - Look at the assistant configuration files to see if the URL is correct
   - Run the update script manually to update the configuration files

3. **Restart the VSCode MCP server**:
   - Use the Command Palette to stop and start the server
   - This will trigger the update script to run

## Related Documentation

- [Connect Hosted Codespace Assistant to Local MCP](connect-hosted-codespace-assistant-to-local-mcp.md)
