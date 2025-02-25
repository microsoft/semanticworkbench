# filesystem MCP Server

Cross platform file system server

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
uv run -m mcp_server.start
```

For SSE transport:

```bash
uv run -m mcp_server.start --transport sse --port 6060
```

The SSE URL is:

```bash
http://127.0.0.1:6666/sse
```

## Tools Available

### `read_file`
Reads the contents of a specific file.

### `write_file`
Writes content to a specified file path. Creates the file if it does not exist.

### `list_directory`
Lists all files and subdirectories within a specified directory.

### `create_directory`
Creates a new directory or ensures an existing one remains accessible.

### `edit_file`
Edits the contents of a text file with specified replacements. Supports a dry run mode to preview changes without applying them.

### `search_files`
Recursively searches for files matching a pattern across subdirectories.

### `get_file_info`
Retrieves and displays detailed metadata about a specified file or directory.

### `read_multiple_files`
Reads the content of multiple files simultaneously and returns their contents in a dictionary. Files not accessible are marked with error messages.

### `move_file`
Moves or renames a file or directory from a source path to a target destination.

### `list_allowed_directories`
Returns a list of directories that the server is permitted to access.


## Client Configuration

To use this MCP server in your setup, consider the following configuration:

### Stdio

```json
{
  "mcpServers": {
    "mcp-server-filesystem": {
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
    "mcp-server-filesystem": {
      "command": "http://127.0.0.1:6060/sse",
      "args": []
    }
  }
}
```
