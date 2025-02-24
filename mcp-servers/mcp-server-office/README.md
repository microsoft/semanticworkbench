# MCP Server for Interaction with Office Apps

This is a [Model Context Protocol](https://github.com/modelcontextprotocol) (MCP) server project.

**Warning**: Be VERY careful with open Word or PowerPoint apps. Your content may be unexpectedly modified or deleted.

## Setup and Installation

Simply run:

```bash
make
```

To create the virtual environment and install dependencies.

### Building the Standalone Executable (Windows Only)

To build the standalone executable for this project, you must:

1. Ensure you are on a **Windows system**.
2. Install the development dependencies (including PyInstaller):
   ```bash
   make
   ```
3. Run the build command to generate the executable:
   ```bash
   make package
   ```

This will create a `mcp-server-office.exe` file inside the `dist/` folder.

### Running the Standalone Executable

Once built, the executable can be run by simply double-clicking it, or from the command prompt:

```bash
./dist/mcp-server-office.exe
```

The server will start in SSE mode and run on port `25566`. To expose the server publicly, use the provided batch file (`run_with_devtunnel.bat`) to set up a Dev Tunnel and start the server.

---

### Running the Server

Use the VSCode launch configuration, or run manually:

Defaults to stdio transport:

```bash
uv run -m mcp_server.start
```

For SSE transport:

```bash
uv run -m mcp_server.start --transport sse --port 25566
```

If you need a public-facing server, use the `--use-ngrok-tunnel` option:

```bash
uv run -m mcp_server.start --use-ngrok-tunnel
```

or for .exe:

```bash
mcp-server-office.exe --use-ngrok-tunnel
```

The SSE URL is:

```bash
http://127.0.0.1:25566/sse
```

## Client Configuration

To use this MCP server in your setup, consider the following configuration:

### Stdio

```json
{
  "mcpServers": {
    "mcp-server-word": {
      "command": "uv",
      "args": ["run", "-m", "mcp_server.start"]
    }
  }
}
```

### SSE

```json
{
  "mcpServers": {
    "mcp-server-word": {
      "command": "http://127.0.0.1:25566/sse",
      "args": []
    }
  }
}
```
