# Whiteboard Memory MCP Server

Stores working memory in a format analogous to a whiteboard

This is a [Model Context Protocol](https://github.com/modelcontextprotocol) (MCP) server project.

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
uv run mcp-server-memory-whiteboard
```

For SSE transport:

```bash
uv run mcp-server-memory-whiteboard --transport sse --port
```

The SSE URL is:

```bash
http://127.0.0.1:/sse
```

## Client Configuration

To use this MCP server in your setup, consider the following configuration:

### Stdio

```json
{
  "mcpServers": {
    "mcp-server-memory-whiteboard": {
      "command": "uv",
      "args": ["run", "-m", "mcp_server_memory_whiteboard.start"]
    }
  }
}
```

### SSE

```json
{
  "mcpServers": {
    "mcp-server-memory-whiteboard": {
      "command": "http://127.0.0.1:/sse",
      "args": []
    }
  }
}
```
