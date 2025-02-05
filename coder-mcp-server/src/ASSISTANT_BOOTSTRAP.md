# ASSISTANT_BOOTSTRAP.md: Onboarding for Codespace Assistant: Coder MCP Server

## 1. Introduction

Welcome to the Codespace Assistant: Coder MCP Server project! This VSCode extension serves as an MCP (Model Context Protocol) server integrated directly within VSCode. Its primary function is to expose a coding diagnostic tool (the `code_checker`) that aggregates diagnostic messages (similar to those shown in VSCode’s Problems panel) and makes them accessible to an external AI assistant via Server-Sent Events (SSE).

## 2. Project Overview

The Codespace Assistant: Coder MCP Server is designed to:

- **Automatically Start:** Activate on VSCode startup (using `"activationEvents": ["*"]` in package.json) so that the MCP server runs without manual intervention.
- **Expose an MCP Server:** Instantiate an MCP server using the TypeScript SDK (`@modelcontextprotocol/sdk`) within the extension.
- **Provide Diagnostic Tools:** Register a `code_checker` tool that retrieves diagnostics (errors/warnings) from VSCode's built-in language services, filtering out files without issues.
- **Communicate via SSE:** Run an Express-based HTTP server that listens on port 6010, providing a GET `/sse` endpoint (to establish a long-lived SSE connection) and a POST `/messages` endpoint for incoming MCP messages.
- **Log Activity:** All activity, including server startup, SSE connection status, and message handling events, is logged to an output channel named **"MCP Server Logs"**—this aids in debugging and ensures transparency of operations.

## 3. Project Structure

- **`src/extension.ts`**: Main extension code. Sets up the MCP server, registers tools (e.g., `code_checker`), and initializes SSE endpoints via an Express app.
- **`package.json`**: Contains all project metadata, scripts, dependencies, and contributions (commands). Note that we use `"activationEvents": ["*"]` to force immediate activation of the extension.
- **`webpack.config.js`, `tsconfig.json`, `.vscode/`**: Additional configuration files supporting the build process, TypeScript compilation, and VSCode debugging tasks.

## 4. Setup and Installation

1. **Install Dependencies:**
   Use your preferred package manager (pnpm is recommended) to install all project dependencies:

   ```bash
   pnpm install
   ```

2. **Build the Extension:**
   Compile the extension using:

   ```bash
   pnpm run compile
   ```

   Alternatively, use:

   ```bash
   pnpm run watch
   ```

   for automatic recompilation during development.

3. **Launch the Extension:**
   Press `F5` in VSCode to start the Extension Development Host. The MCP server will automatically start, and its logs will appear in the **"MCP Server Logs"** output channel.

## 5. Testing the MCP Server

You can test the SSE endpoints using `curl`:

### Step A: Establish the SSE Connection

Open a terminal and run:

```bash
curl -N http://127.0.0.1:6010/sse
```

This will keep the connection open and simulate an external assistant connecting via SSE. You should see the endpoint URL (including a `sessionId`) in the output.

### Step B: Send an Initialize Request

Using the session ID received from the SSE connection, open a second terminal and send a POST request:

```bash
curl -X POST "http://127.0.0.1:6010/messages?sessionId=<your-session-id>" \
-H "Content-Type: application/json" \
-d '{
  "jsonrpc": "2.0",
  "method": "initialize",
  "id": 0,
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": { "roots": { "listChanged": true } },
    "clientInfo": { "name": "mcp", "version": "0.1.0" },
    "workspace": { "folders": [] }
  }
}'
```

If working correctly, the MCP server will process the initialization without re-reading the request stream (thanks to passing `req.body`) and return a valid response.

## 6. Important Implementation Notes

- **Stream Handling and Middleware:**

  - When using `express.json()`, the middleware consumes the request stream. Therefore, the pre-parsed `req.body` is passed to `handlePostMessage(req, res, req.body)` to avoid "stream is not readable" errors.
  - This is a critical part of the implementation and needs to be preserved in future modifications.

- **Activation Events:**
  - Currently, the extension uses `"activationEvents": ["*"]` in package.json, which forces activation on startup. While this may impact performance slightly, it is necessary to ensure that the MCP server is running as soon as VSCode starts.
  - Future enhancements may include more refined activation criteria based on workspace contents or file types.

## 7. Future Enhancements

- **Enhanced Diagnostic Tools:**
  - Extend `code_checker` to support recursive checks and additional diagnostic tools.
- **Multi-Language Support:**
  - Integrate similar tools for various languages (e.g., Python, JavaScript) using respective language servers.
- **Improved SSE Protocol Handling:**
  - Enhance session management and error handling within the SSE transport layer.
- **UI Enhancements:**
  - Provide additional commands for in-UI management of diagnostic data and MCP server controls.
- **Documentation Updates:**
  - Ensure all changes and new features are documented both in code comments and within this bootstrap document.

---

Thank you for using Codespace Assistant: Coder MCP Server. This document should serve as the definitive guide for onboarding, current project behavior, and future directions. Keep it updated as the project evolves.
