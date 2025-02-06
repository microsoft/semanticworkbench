# VSCode MCP Server

## Overview

The **VSCode MCP Server** is a VSCode extension that acts as a Model Context Protocol (MCP) server integrated directly within VSCode. Its primary purpose is to expose a coding diagnostic tool—namely, the `code_checker`—which aggregates diagnostic messages (similar to those displayed in VSCode’s Problems panel) and makes them accessible to an external AI assistant via Server-Sent Events (SSE). This allows your assistant to invoke MCP methods and retrieve timely diagnostic information from your workspace.

## Features

- **Automatic Startup:**  
  The extension activates automatically on VSCode startup (using `"activationEvents": ["*"]` in `package.json`), ensuring the MCP server is always running without manual intervention.

- **MCP Server Integration:**  
  Built using the MCP TypeScript SDK (`@modelcontextprotocol/sdk`), the extension instantiates an MCP server that registers diagnostic tools and handles MCP protocol messages.

- **Diagnostic Tool (`code_checker`):**  
  The registered `code_checker` tool collects diagnostics from VSCode’s built-in language services, filtering out files without errors. When invoked, it returns a formatted JSON object containing diagnostic information (only for files with issues).

- **SSE Communication:**  
  An Express-based HTTP server runs on port 6010, exposing:

  - A **GET `/sse`** endpoint to establish a long-lived Server-Sent Events (SSE) connection.
  - A **POST `/messages`** endpoint for receiving MCP messages from external clients (such as your AI assistant).  
    Special care is taken to handle the request body properly—thanks to passing the already-parsed `req.body` to avoid stream-related errors.

- **Verbose Logging:**  
  All activity, including server startup, SSE connection status, and message handling events, is logged to an output channel named **"MCP Server Logs"** to aid debugging and transparency.

## Project Structure

```
vscode-mcp-server/
├── .vscode/                  # VSCode workspace and debugging configurations
├── node_modules/             # Installed dependencies
├── package.json              # Project metadata and scripts
├── pnpm-lock.yaml            # Dependency lock file
├── src/
│   └── extension.ts          # Main extension code setting up the MCP server, tools, and SSE endpoints
├── tsconfig.json             # TypeScript configuration
├── webpack.config.js         # Webpack configuration for bundling the extension
└── README.md                 # This file
```

## Setup and Installation

1. **Install Dependencies:**  
   Ensure you have Node.js (v16 or higher) and pnpm installed. Then, from the project directory, run:

   ```bash
   pnpm install
   ```

2. **Compile the Extension:**  
   To build the extension, execute:
   ```bash
   pnpm run compile
   ```
   You can also run:
   ```bash
   pnpm run watch
   ```
   to automatically recompile code changes during development.

## Running the Extension

1. **Start Debugging:**  
   Open the project in VSCode, then press **F5** to launch the Extension Development Host. This will automatically activate the extension based on the `"activationEvents": ["*"]` setting.

2. **MCP Server Operation:**  
   On activation, the extension:
   - Starts the MCP server which registers the `code_checker` tool.
   - Sets up an Express HTTP server on port **6010** with:
     - **GET `/sse`:** To establish an SSE connection (external clients connect here).
     - **POST `/messages`:** To process incoming MCP protocol messages.
   - Outputs all activity to the **"MCP Server Logs"** channel (which will be auto-shown).

## Testing the MCP Server

You can use `curl` to test the service:

### Step 1: Establish the SSE Connection

Open Terminal 1 and run:

```bash
curl -N http://127.0.0.1:6010/sse
```

You should see output similar to:

```
event: endpoint
data: /messages?sessionId=your-session-id
```

### Step 2: Send an Initialization Request

In Terminal 2, using the session ID obtained from Terminal 1 (if needed), send a POST request (include any required fields such as workspace if necessary):

```bash
curl -X POST "http://127.0.0.1:6010/messages?sessionId=your-session-id" \
-H "Content-Type: application/json" \
-d '{
  "jsonrpc": "2.0",
  "method": "initialize",
  "id": 0,
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "roots": { "listChanged": true }
    },
    "clientInfo": {
      "name": "mcp",
      "version": "0.1.0"
    },
    "workspace": {
      "folders": []
    }
  }
}'
```

If everything is configured correctly, the MCP server should process your initialization message without errors.

## Following extension guidelines

Ensure that you've read through the extensions guidelines and follow the best practices for creating your extension.

- [Extension Guidelines](https://code.visualstudio.com/api/references/extension-guidelines)
