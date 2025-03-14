# Filesystem Edit MCP Server

Allows for robust editing of files like Markdown and LaTeX

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
uv run mcp-server-filesystem-edit
```

For SSE transport:

```bash
uv run mcp-server-filesystem-edit --transport sse --port 25567
```

The SSE URL is:

```bash
http://127.0.0.1:25567/sse
```

## Client Configuration

To use this MCP server in your setup, consider the following configuration:

### Stdio

```json
{
  "mcpServers": {
    "mcp-server-filesystem-edit": {
      "command": "uv",
      "args": ["run", "-m", "mcp_server_filesystem_edit.start"]
    }
  }
}
```

### SSE

```json
{
  "mcpServers": {
    "mcp-server-filesystem-edit": {
      "command": "http://127.0.0.1:25567/sse",
      "args": []
    }
  }
}
```
