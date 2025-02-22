# MCP Server for Interaction with Office Apps

This is a [Model Context Protocol](https://github.com/modelcontextprotocol) (MCP) server project.

**Warning**: Be VERY careful with open Word or PowerPoint apps. Your content may be unexpectedly modified or deleted.

## Setup and Installation

Simply run:

```bash
make
```

To create the virtual environment and install dependencies.

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
