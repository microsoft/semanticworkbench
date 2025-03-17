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


### Setting Allowed Directories

The server uses "allowed directories" for security purposes. There are two ways to configure them:

1. **Command line arguments**: Using `--allowed_directories` parameter (required for stdio transport)
2. **Root configuration**: For SSE transport, the server can use the roots defined by the client

When using the root configuration approach, the MCP client sets the accessible directories through the session's `list_roots()` mechanism so each allowed directory must be set in the client's root configuration.


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
