# Bing Search MCP Server

Searches the web and reads links

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
uv run mcp-server-bing-search
```

For SSE transport:

```bash
uv run mcp-server-bing-search --transport sse --port 6030
```

The SSE URL is:

```bash
http://127.0.0.1:6030/sse
```

## Client Configuration

To use this MCP server in your setup, consider the following configuration:

### Stdio

```json
{
  "mcpServers": {
    "mcp-server-bing-search": {
      "command": "uv",
      "args": ["run", "-m", "mcp_server_bing_search.start"]
    }
  }
}
```

### SSE

```json
{
  "mcpServers": {
    "mcp-server-bing-search": {
      "command": "http://127.0.0.1:6030/sse",
      "args": []
    }
  }
}
```
