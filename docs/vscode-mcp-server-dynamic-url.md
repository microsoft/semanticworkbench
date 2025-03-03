# VSCode MCP Server Dynamic URL

## Overview

This document explains the implementation and usage of the dynamic VSCode MCP server URL feature in the Semantic Workbench. This feature enables the assistant to automatically connect to the VSCode MCP server regardless of the port it's running on, improving reliability and user experience.

## Background

Previously, the VSCode MCP server URL was hardcoded as `http://127.0.0.1:6010/sse` in the assistant configuration. This caused issues when:

1. The port `6010` was already in use by another application
2. The VSCode extension started the server on a different port
3. Users needed to manually update the configuration each time the port changed

## Implementation

The dynamic URL feature solves these issues by:

1. Storing the VSCode MCP server URL in a global variable that can be updated at runtime
2. Providing utility functions to access and update this URL
3. Automatically updating the assistant configuration when the server starts or stops
4. Using a dynamic port allocation system that avoids port conflicts

### Key Components

- **Global Variable**: A centralized storage (`vscodeMcpServerUrl`) for the current VSCode MCP server URL
- **Access Functions**: 
  - `getMcpServerUrl()`: Retrieves the current URL with fallback to default
  - `setMcpServerUrl(url)`: Updates the URL when the server starts or changes ports
  - `resetMcpServerUrl()`: Resets the URL to the default value
- **Configuration Helpers**:
  - `updateConfigWithMcpServerUrl(config)`: Updates the assistant configuration with the current URL
  - `hasVscodeMcpServer(config)`: Checks if a configuration has a VSCode MCP server
  - `getVscodeMcpServerConfig(config)`: Gets the VSCode MCP server configuration
- **VSCode Extension**: Starts the MCP server on a dynamic port and updates the URL
- **Update Script**: A CLI tool to manually update or reset the URL (`update-vscode-mcp-url.js`)
- **Test Script**: A utility to test the connection to the server (`test-vscode-mcp.js`)

### System Flow

1. When the VSCode extension activates:
   - It creates an HTTP server on port 0 (letting the OS assign an available port)
   - The SSE transport is configured to use this HTTP server
   - Once the server is listening, the actual port number is obtained
   - The extension calls `updateWorkbenchMcpServerUrl(port)` to notify the workbench

2. The notification process:
   - The extension executes the `update-vscode-mcp-url.js` script
   - The script imports and calls `setMcpServerUrl(url)` from the workbench service
   - This updates the global `vscodeMcpServerUrl` variable

3. When the assistant needs the URL:
   - It calls `getMcpServerUrl()` to get the current URL
   - The function returns the current URL or falls back to the default

4. When the extension deactivates:
   - It executes the update script with "reset" parameter
   - This calls `resetMcpServerUrl()` to restore the default URL
### Related Changes

This implementation is related to the [SamplingFnT type error fix](./SAMPLING_FN_TYPE_ERROR_FIX.md), as both improve the robustness of the MCP client session handling. 

The SamplingFnT type error fix (using the TypeScript spread operator `...` for type parameters) ensures compatibility with different versions of the MCP package, resolving the `TypeError: Optional[SamplingFnT] is not compatible with Optional[SamplingFnT[...]]` issue that was occurring. Meanwhile, the dynamic URL feature ensures reliable connection to the VSCode MCP server regardless of the port it's running on.

## Usage

### For Developers

When developing assistants that need to connect to the VSCode MCP server:

1. Import the `getMcpServerUrl` function from the workbench service
2. Use this function to get the current VSCode MCP server URL
3. Pass this URL to the assistant configuration
4. Update the configuration when needed using `updateConfigWithMcpServerUrl(config)`

Example:

```typescript
import { getMcpServerUrl } from 'services/workbench';

const vscodeMcpServerUrl = getMcpServerUrl();
const config = {
  // ... other configuration
  mcpServers: [
    {
      key: "vscode",
      command: vscodeMcpServerUrl,
      args: [],
    },
    // ... other servers
  ]
};
```

### For Users

Users benefit from this feature automatically without any manual configuration:

1. When the VSCode extension starts the MCP server, it automatically updates the URL
2. The assistant uses the updated URL to connect to the server
3. If the server stops or changes ports, the URL is updated accordingly

### Implementation Details

#### VSCode Extension

The VSCode extension (`mcp-server-vscode`) implements:

1. Dynamic port allocation:
   ```typescript
   httpServer.listen(0, '127.0.0.1', () => {
       const addressInfo = httpServer.address() as { port: number };
       const port = addressInfo.port;
       // ... set up SSE transport
   });
   ```

2. URL notification:
   ```typescript
   async function updateWorkbenchMcpServerUrl(port: number) {
       // ... execute update script with the new URL
   }
   ```
   
   ```

3. URL reset on deactivation:
   ```typescript
   export function deactivate() {
       // ... execute update script with 'reset' parameter
   }
   ```

#### Workbench Service

The workbench service (`workbench-app/src/services/workbench`) implements:

1. URL management:
   ```typescript
   // Global variable to store the current URL
   let vscodeMcpServerUrl: string = DEFAULT_VSCODE_MCP_SERVER_URL;
   
   // Functions to get, set, and reset the URL
   export function getMcpServerUrl(): string { ... }
   export function setMcpServerUrl(url: string): void { ... }
   export function resetMcpServerUrl(): void { ... }
   ```

2. Configuration integration:
   ```typescript
   export function updateConfigWithMcpServerUrl(config: AssistantConfig, url?: string): AssistantConfig { ... }
   ```

## Testing

To test the dynamic URL feature:

1. Start the VSCode extension with the MCP server enabled
2. Run the test script: `node scripts/test-vscode-mcp.js`
3. Verify that the script can connect to the server and execute commands
4. Stop and restart the server on a different port to confirm the URL updates correctly

The test script connects to the server and lists available tools:

```javascript
const url = getMcpServerUrl();
console.log(`Testing VSCode MCP server at: ${url}`);

// Connect to the server and list tools
const [readStream, writeStream] = await sse_client(url);
const session = new ClientSession(readStream, writeStream);
// ...
const toolsResult = await session.list_tools();
```

## Troubleshooting

Common issues and solutions:

1. **Connection refused**: The VSCode MCP server may not be running or the URL is incorrect.
   - Check if the VSCode extension is active
   - Run `node scripts/test-vscode-mcp.js` to verify connectivity

2. **Port conflicts**: If the default port is in use, the VSCode extension will automatically use a different port.
   - No manual intervention is needed as the system handles this automatically

3. **URL not updating**: If the assistant can't connect to the VSCode MCP server:
   - Restart the VSCode extension
   - Run `node scripts/update-vscode-mcp-url.js reset` to restore the default URL

## Future Enhancements

Future improvements may include:

1. Health checking to detect server disconnections
2. Automatic reconnection when the server becomes available again
3. Support for multiple VSCode instances with different MCP servers running simultaneously
4. Configuration UI in the workbench to view and modify the current server URL
5. More robust error handling and recovery mechanisms
3. Support for multiple VSCode instances with different MCP servers
4. Configuration UI to view and modify the current server URL