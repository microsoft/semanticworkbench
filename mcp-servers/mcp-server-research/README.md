# MCP GIPHY Server

## Overview

...TBD

## Features

...TBD

## Development Principles

- **Modularity and Conciseness:** Each code file should not exceed one page in length, ensuring concise and focused code.
- **Semantic Names:** Use meaningful names for functions and modules to enhance understanding and maintainability.
- **Organized Structure:** Maintain a well-organized structure, breaking down functionality into clear and manageable components.

## Setup and Installation

Simply run:

```bash
make
```

To create the virtual environment and install dependencies.

### Running the Server

Use the VSCode launch configuration, or run manually:

```bash
python server/main.py --transport stdio
```

For SSE transport:

```bash
python server/main.py --transport sse --port 6010
```

The SSE URL is:

```bash
http://127.0.0.1:6010/sse
```

## Client Configuration

To use this MCP server in your setup, consider the following configuration:

### UV - Local files

```json
{
  "mcpServers": {
    "research": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/project/mcp-server-research",
        "run",
        "server/main.py"
      ],
      "env": {
        "SERP_API_KEY": "YOUR_SERP_API_KEY"
      }
    }
  }
}
```

### SSE

```json
{
  "mcpServers": {
    "research": {
      "command": "http://127.0.0.1:6010/sse",
      "args": []
    }
  }
}
```

Ensure that `SERP_API_KEY` is set in your environment so that the server can authenticate with the Serp API.
