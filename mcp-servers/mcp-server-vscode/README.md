# VSCode MCP Server

## Overview

The **VSCode MCP Server** is a VSCode extension that acts as a Model Context Protocol (MCP) server integrated directly within VSCode. Its primary purpose is to expose a coding diagnostic tool—namely, the `code_checker`—which aggregates diagnostic messages (similar to those displayed in VSCode’s Problems panel) and makes them accessible to an external AI assistant via Server-Sent Events (SSE). This allows your assistant to invoke MCP methods and retrieve timely diagnostic information from your workspace.

## Features

-   **Automatic Startup:**
    The extension activates automatically on VSCode startup (using `"activationEvents": ["*"]` in `package.json`), ensuring the MCP server is always running without manual intervention.

-   **MCP Server Integration:**
    Built using the MCP TypeScript SDK (`@modelcontextprotocol/sdk`), the extension instantiates an MCP server that registers diagnostic tools and handles MCP protocol messages.

-   **Diagnostic Tool (`code_checker`):**
    The registered `code_checker` tool collects diagnostics from VSCode’s built-in language services, filtering out files without errors. When invoked, it returns a formatted JSON object containing diagnostic information (only for files with issues).

-   **Focus Editor Tool (`focus_editor`)**: Opens a specific file in the VSCode editor and navigates to a designated line and column. Useful for bringing files into visual focus for the user but does not include file content in the tool call result.
-   **Search Symbol Tool (`search_symbol`)**: Searches for symbols in the workspace, using "Go to Definition" primarily, with a fallback to text search (similar to Ctrl+Shift+F). Can optionally open the results in the editor using the `focus_editor` tool.

-   **Debug Session Management Tools:**
    The extension provides tools to manage VSCode debug sessions directly using MCP:

    -   `list_debug_sessions`: Retrieve all active debug sessions in the workspace.
    -   `start_debug_session`: Start a new debug session with the provided configuration.
    -   `stop_debug_session`: Stop debug sessions matching a specific session name.
    -   `restart_debug_session`: Restart a debug session by stopping it and then starting it with the provided configuration (new!).

-   **SSE Communication:**
    An Express-based HTTP server runs on a configurable port (default: 6010) and dynamically handles port conflicts. It exposes:

    -   A **GET `/sse`** endpoint to establish a long-lived Server-Sent Events (SSE) connection. If the default port (6010) is unavailable, users can configure a new one via their VSCode settings (see Dynamic Port Configuration below).
    -   A **POST `/messages`** endpoint for receiving MCP messages from external clients (such as your AI assistant).
        Special care is taken to handle the request body properly—thanks to passing the already-parsed `req.body` to avoid stream-related errors.

-   **Verbose Logging:**
    All activity, including server startup, SSE connection status, and message handling events, is logged to an output channel named **"VSCode MCP Server"** to aid debugging and transparency.

## Using the Extension from Claude Desktop (MCP Client)

To use the VSCode MCP Server with Claude Desktop, you need to configure Claude Desktop to connect to the MCP server running in VSCode. Since the implementation of the MCP server uses SSE transport, and Claude Desktop only supports stdio transport, you need to use a [mcp-proxy](https://github.com/sparfenyuk/mcp-proxy) to bridge the communication between the two.

1. **Install MCP Proxy:**

    - Option 1: With uv (recommended)

        ```
        uv tool install mcp-proxy
        ```

    - Option 2: With pipx (alternative)

        ```
        pipx install mcp-proxy
        ```

2. **Configure Claude Desktop:**

    - Open Claude Desktop and navigate to the **File** > **Settings** > **Developer** tab.
    - Click **Edit Config** to open the config file, launch your desired editor to modify the config file contents.
    - Add a new entry to **mcpServers** with the following details:

        ```json
        {
            "mcpServers": {
                "vscode": {
                    "command": "mcp-proxy",
                    "args": ["http://127.0.0.1:6010/sse"]
                }
            }
        }
        ```

3. **Restart Claude Desktop:**

    - You **must** restart Claude Desktop for the changes to take effect by using the **File** > **Exit** option.
    - NOTE: This is different than just closing the window or using **File** > **Close**, which leaves the application running in the background.
    - After existing and then starting again, Claude Desktop should now be able to connect to the MCP server running in VSCode.

## MCP Server Management

The MCP Server status can now be managed directly from the Command Palette:

1. **Stop MCP Server** (`mcpServer.stopServer`): Stops the currently running MCP Server.
2. **Start MCP Server** (`mcpServer.startServer`): Starts the server on the configured or next available port.

These commands help manage server lifecycle dynamically, without requiring a VSCode restart.

## Dynamic Port Configuration

If the port is already in use, the extension will suggest the next available port and apply it dynamically. Logs reflecting the selected port can be found in the **MCP Server Logs** output channel.

Users can configure or change the MCP Server's port at runtime using the Command Palette:

1. Open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P` on macOS).
2. Search for `Set MCP Server Port`.
3. Enter the desired port number in the input box and confirm.

The server will dynamically restart on the newly selected port, and the configuration will be updated for future sessions.

The HTTP server port can also be set via VSCode settings:

1. Open VSCode settings (`File > Preferences > Settings` or `Ctrl+,`).
2. Search for `mcpServer.port`.
3. Set your desired port number.
4. Restart VSCode for the changes to take effect.

## MCP Server Automatic Startup

The MCP Server starts automatically on VSCode activation by default. To disable this feature:

1. Open VSCode settings (`File > Preferences > Settings` or `Ctrl+,`).
2. Search for `mcpServer.startOnActivate`.
3. Toggle the setting to `false`.

This can be useful if you prefer to start the server manually using the `Start MCP Server` command.

## Extension Development

Steps for developing and debugging the extension, source code available at [GitHub](https://github.com/microsoft/semanticworkbench/tree/main/mcp-servers/mcp-server-vscode).

### Prerequisites

1. **Clone the Repository:**
   Clone the Semantic Workbench repository to your local machine:

    ```bash
    git clone https://github.com/microsoft/semanticworkbench.git
    ```

2. **Navigate to the Project Directory:**

    ```bash
    cd semanticworkbench/mcp-servers/mcp-server-vscode
    ```

3. **Install Dependencies:**
   Ensure you have Node.js (v16 or higher) and pnpm installed. Then, from the project directory, run:

    ```bash
    pnpm install
    ```

4. **Package the Extension:**
   To package the extension, execute:
    ```bash
    pnpm run package-extension
    ```
    This will generate a `.vsix` file in the project root.

### Installing the Extension Locally

1. **Open Your Main VSCode Instance:**

    Launch your main VSCode (outside the Extension Development Host).

2. **Install the VSIX Package:**

    - Press Ctrl+Shift+P (or Cmd+Shift+P on macOS) to open the Command Palette.
    - Type and select "Extensions: Install from VSIX...".
    - Navigate to and select the generated .vsix file.

3. **Reload and Verify:**

    After installation, reload VSCode (via "Developer: Reload Window" from the Command Palette) and verify that the extension is active. Check the "MCP Server Logs" output channel to see logs confirming that the MCP server has started and is listening on the configured port (default: 6010, or the next available one).

### Debugging the Extension

1. **Start Debugging:**
   Open the project in VSCode, then press **F5** to launch the Extension Development Host. This will automatically activate the extension based on the `"activationEvents": ["*"]` setting.

2. **MCP Server Operation:**
   On activation, the extension:
    - Starts the MCP server which registers the `code_checker` tool.
    - Sets up an Express HTTP server on port **6010** with:
        - **GET `/sse`:** To establish an SSE connection (external clients connect here).
        - **POST `/messages`:** To process incoming MCP protocol messages.
    - Outputs all activity to the **"MCP Server Logs"** channel (which will be auto-shown).

### Installing the Extension Locally

1. **Open Your Main VSCode Instance:**

    Launch your main VSCode (outside the Extension Development Host).

2. **Install the VSIX Package:**

    - Press Ctrl+Shift+P (or Cmd+Shift+P on macOS) to open the Command Palette.
    - Type and select "Extensions: Install from VSIX...".
    - Navigate to and select the generated .vsix file.

3. **Reload and Verify:**

    After installation, reload VSCode (via "Developer: Reload Window" from the Command Palette) and verify that the extension is active. Check the "MCP Server Logs" output channel to see logs confirming that the MCP server has started and is listening on port 6010.

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
