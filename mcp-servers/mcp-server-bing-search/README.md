# Bing Search MCP Server

Searches the web and reads links

This is a [Model Context Protocol](https://github.com/modelcontextprotocol) (MCP) server project.

## Tools

### `search(query: str) -> str`

- Calls the Bing Search API with the provided query.
- Processes each URL from the search results:
  - Gets the content of the page
  - Converts it to Markdown using Markitdown
  - Parses out links separately. Caches a unique hash to associate with each link.
  - (Optional, on by default) Uses sampling to select the most important links to return.
  - (Optional, on by default) Filters out the Markdown content to the most important parts.
- Returns the processed content and links as a LLM-friendly string.

### `click(hashes: list[str]) -> str`

- Takes a list of hashes (which originate from the `search` tool).
- For each hash gets the corresponding URL from the local cache.
- Then does the same processing as `search` for each URL and returns a similar LLM-friendly string.

## Setup and Installation

Simply run:

```bash
make
```

To create the virtual environment and install dependencies.

### Setup Environment Variables

Create a `.env` file based on `.env.sample` and populate it with:

- `BING_SEARCH_API_KEY`
- `ASSISTANT__AZURE_OPENAI_ENDPOINT` - This is necessary if you want to post process web content.

### Running the Server

Use the VSCode launch configuration, or run manually:

Defaults to stdio transport:

```bash
uv run mcp-server-bing-search
```

For SSE transport:

```bash
uv run mcp-server-bing-search --transport sse --port 6030
```

The SSE URL is:

```bash
http://127.0.0.1:6030/sse
```

## Client Configuration

To use this MCP server in your setup, consider the following configuration:

### Stdio

```json
{
  "mcpServers": {
    "mcp-server-bing-search": {
      "command": "uv",
      "args": ["run", "-m", "mcp_server_bing_search.start"]
    }
  }
}
```

### SSE

```json
{
  "mcpServers": {
    "mcp-server-bing-search": {
      "command": "http://127.0.0.1:6030/sse",
      "args": []
    }
  }
}
```
