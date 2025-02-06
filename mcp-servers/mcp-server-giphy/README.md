# MCP GIPHY Server

## Overview

This project implements a Model Context Protocol (MCP) server integration with the GIPHY API. The server allows an assistant to submit recent chat history ('context') and a search term to retrieve a list of candidate results from GIPHY and load their image data.

## Features

- **Search and Retrieve:** Uses the GIPHY API to search for images based on a provided search term.
- **Sampling:** Employs the MCP "sampling" feature to request the assistant to choose the most appropriate image for the context.
- **Integration:** The selected GIPHY image and its metadata are returned to the original assistant tool call, enabling it to be included in assistant responses to users.

## Development Principles

- **Modularity and Conciseness:** Each code file should not exceed one page in length, ensuring concise and focused code.
- **Semantic Names:** Use meaningful names for functions and modules to enhance understanding and maintainability.
- **Organized Structure:** Maintain a well-organized structure, breaking down functionality into clear and manageable components.

## Project Structure

```
/mcp-server-giphy
│
├── README.md
├── server
│   ├── __init__.py
│   ├── main.py
│   ├── giphy_search.py
│   ├── sampling.py
│   └── response_handling.py
```

## Plan

1. **Initialize Project Structure:** Create modules and stub functions.
2. **Giphy Search Implementation:** Implement the search functionality using the GIPHY API.
3. **Sampling Feature:** Develop the sampling mechanism to choose an image.
4. **Response Handling:** Ensure the proper integration and response to the assistant tool call.

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
python server/main.py --transport sse --port 6000
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
      "args": [
        "--directory",
        "/path/to/project/mcp-server-giphy",
        "run",
        "server/main.py"
      ],
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
