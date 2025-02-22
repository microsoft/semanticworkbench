# Fusion MCP Server

Fusion MCP Server for help creating 3D models

This is a [Model Context Protocol](https://github.com/modelcontextprotocol) (MCP) server project.

## Setup and Installation

Simply run:

```bash
pip install -r requirements.txt --target ./vendor
```

To create the virtual environment and install dependencies.

### Running the Server

Use the VSCode launch configuration, or run manually:

Defaults to stdio transport:

```bash
python -m mcp_server.start
```

For SSE transport:

```bash
python -m mcp_server.start --transport sse --port 6050
```

The SSE URL is:

```bash
http://127.0.0.1:6050/sse
```

## Client Configuration

To use this MCP server in your setup, consider the following configuration:

### Stdio

```json
{
  "mcpServers": {
    "mcp-server-fusion": {
      "command": "python",
      "args": ["run", "-m", "mcp_server.start"]
    }
  }
}
```

### SSE

```json
{
  "mcpServers": {
    "mcp-server-fusion": {
      "command": "http://127.0.0.1:6050/sse",
      "args": []
    }
  }
}
```
