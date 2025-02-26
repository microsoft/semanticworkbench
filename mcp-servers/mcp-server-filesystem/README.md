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

The server requires specifying at least one allowed directory (for security reasons).

For stdio transport, specify directories using the --allowed_directories argument:

```bash
uv run -m mcp_server.start --allowed_directories /path1 /path2 /path3
```

For SSE transport, you can start the server without specifying directories:

```bash
uv run -m mcp_server.start --transport sse --port 6060
```

But when connecting, you must include the allowed directories as URL parameters:

```
http://127.0.0.1:6060/sse?allowed_directories=/path1,/path2,/path3
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
      "args": ["run", "-m", "mcp_server.start", "--allowed_directories", "/path1", "/path2"]
    }
  }
}
```

### SSE

```json
{
  "mcpServers": {
    "mcp-server-filesystem": {
      "command": "http://127.0.0.1:6060/sse?allowed_directories=/path1,/path2",
      "args": []
    }
  }
}
```

### SSE with Separate Arguments

For clients that support it, you can specify the allowed directories using the args array:

```json
{
  "mcpServers": {
    "mcp-server-filesystem": {
      "command": "http://127.0.0.1:6060/sse",
      "args": ["allowed_directories", "/path1", "/path2"]
    }
  }
}
```

In this format, the first argument is the parameter name and subsequent arguments will be joined with commas as the parameter value (if supported by the client).
