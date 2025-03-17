# Open Deep Research Clone MCP Server

Uses the web to research a given topic.

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
uv run mcp-server-open-deep-research-clone
```

For SSE transport:

```bash
uv run mcp-server-open-deep-research-clone --transport sse --port 6061
```

The SSE URL is:

```bash
http://127.0.0.1:45567/sse
```

## Client Configuration

To use this MCP server in your setup, consider the following configuration:

### Stdio

```json
{
  "mcpServers": {
    "mcp-server-open-deep-research-clone": {
      "command": "uv",
      "args": ["run", "-m", "mcp_server_open_deep_research_clone.start"]
    }
  }
}
```

### SSE

```json
{
  "mcpServers": {
    "mcp-server-open-deep-research-clone": {
      "command": "http://127.0.0.1:6061/sse",
      "args": []
    }
  }
}
```
