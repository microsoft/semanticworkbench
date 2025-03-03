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

### Key Components

- **Global Variable**: A centralized storage for the current VSCode MCP server URL
- **Access Function**: A function to retrieve the current URL with fallback to default
- **Update Function**: A function to update the URL when the server starts or changes ports
- **Integration**: Code to update the assistant configuration when the URL changes

### Related Changes

This implementation is related to the [SamplingFnT type error fix](./SAMPLING_FN_TYPE_ERROR_FIX.md), as both improve the robustness of the MCP client session handling. 

The SamplingFnT type error fix (using the TypeScript spread operator `...` for type parameters) ensures compatibility with different versions of the MCP package, resolving the `TypeError: Optional[SamplingFnT] is not compatible with Optional[SamplingFnT[...]]` issue that was occurring. Meanwhile, the dynamic URL feature ensures reliable connection to the VSCode MCP server regardless of the port it's running on.

## Usage

### For Developers

When developing assistants that need to connect to the VSCode MCP server:

1. Import the `getMcpServerUrl` function from the workbench service
2. Use this function to get the current VSCode MCP server URL
3. Pass this URL to the assistant configuration

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

## Testing

To test the dynamic URL feature:

1. Start the VSCode extension with the MCP server enabled
2. Run the test script: `node scripts/test-vscode-mcp.js`
3. Verify that the script can connect to the server and execute commands
4. Stop and restart the server on a different port to confirm the URL updates correctly

## Future Enhancements

Future improvements may include:

1. Health checking to detect server disconnections
2. Automatic reconnection when the server becomes available again
3. Support for multiple VSCode instances with different MCP servers
4. Configuration UI to view and modify the current server URL