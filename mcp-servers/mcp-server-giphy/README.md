# MCP GIPHY Server

## Overview

This project implements a Model Context Protocol (MCP) server integration with the GIPHY API. The server allows an assistant to submit recent chat history ('context') and a search term to retrieve a list of candidate results from GIPHY and load their image data.

## Features

- **Search and Retrieve:** Uses the GIPHY API to search for images based on a provided search term.
- (Future) **Sampling:** Employs the MCP "sampling" feature to request the assistant to choose the most appropriate image for the context.
- **Integration:** The selected GIPHY image and its metadata are returned to the original assistant tool call, enabling it to be included in assistant responses to users.

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
uv run -m mcp_server.start --transport sse --port 6020
```

The SSE URL is:

```bash
http://127.0.0.1:6000/sse
```

## Client Configuration

To use this MCP server in your setup, consider the following configuration:

### UV - Local files

```json
{
  "mcpServers": {
    "giphy-server": {
      "command": "uv",
      "args": ["run", "-m", "mcp_server.start"],
      "env": {
        "GIPHY_API_KEY": "YOUR_GIPHY_API_KEY"
      }
    }
  }
}
```

### SSE

```json
{
  "mcpServers": {
    "giphy-server": {
      "command": "http://127.0.0.1:6000/sse",
      "args": []
    }
  }
}
```

Ensure that `GIPHY_API_KEY` is set in your environment so that the server can authenticate with the GIPHY API.
