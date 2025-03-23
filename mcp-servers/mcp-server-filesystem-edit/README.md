# Filesystem Edit MCP Server

Allows for robust editing Markdown and LaTeX files.

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


### Setting Working Directory
The server uses a single working directory for security purposes. There are two ways to configure them:

1. **Command line arguments**: Using `--allowed_directories` parameter (required for stdio transport) which will use the first directory.
2. **Root configuration**: For SSE transport, the server can use the roots defined by the client and it will use the first valid dir as the working directory. When using this approach, the MCP client makes the working available through the session's `list_roots()` mechanism.


## Tools
### `list_working_directory()`
- Lists the files in the working directory relative to it.
- All other tools will need to provide paths relative to this directory.

### `view_file(path)`
- Reads the content of the file at the given path.

### `edit_file(path, task)`
- Edits the file at the given path with the provided content according to the task.
- Uses sampling to understand things like conversation history and attachments from the client.
- If the file extension is `.md` or `.tex`, special handling is applied.
- All other file types will return an error.
- If `enable-pdflatex` is set, it will compile the LaTeX file using pdflatex and return the output.

### `add_comments(path, comments)`
- Reads the file at the given path, adds comments to the content, and returns suggestions on what to do next.
- Special handling is applied for `.md` and `.tex` files. All other file types will return an error.


### Optional Features
- If you have pdflatex installed on your system and you would like `edit_file` to automatically compile LaTeX files for you,
can provide the argument `--enable-pdflatex` when starting the server.


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
