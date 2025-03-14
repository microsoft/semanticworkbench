# Memory - User Bio MCP Server

Allows saving of memories across conversations related to user interests, preferences, and ongoing projects.

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
uv run mcp-server-memory-user-bio
```

For SSE transport:

```bash
uv run mcp-server-memory-user-bio --transport sse --port 34737
```

The SSE URL is:

```bash
http://127.0.0.1:34737/sse
```

## Client Configuration

To use this MCP server in your setup, consider the following configuration:

### Stdio

```json
{
  "mcpServers": {
    "mcp-server-memory-user-bio": {
      "command": "uv",
      "args": ["run", "-m", "mcp_server_memory_user_bio.start"]
    }
  }
}
```

### SSE

```json
{
  "mcpServers": {
    "mcp-server-memory-user-bio": {
      "command": "http://127.0.0.1:34737/sse",
      "args": []
    }
  }
}
```

## Optional roots

For MCP clients that support specifying roots, such as the Codespace assistant, the
following roots are optional and can be used to customize the behavior of the server:
- `user-timezone`: The user's timezone, which will be used to determine the date a memory was created. URI can be any schema. The host and path will be used as the timezone. For example, `user-timezone://America/New_York` will be used as `America/New_York`.
- `session-id`: The session ID, which will be used to identify the session, for separation of memories by session. URI can be any schema. The host and path will be used as the session ID. For example, `session-id://123456` will be used as `123456`.
