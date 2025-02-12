# Open Deep Research MCP Server

This is a [Model Context Protocol](https://github.com/modelcontextprotocol) (MCP) server that wraps the [HuggingFace Open Deep Research](https://github.com/huggingface/smolagents/tree/main/examples/open_deep_research) project, built on their [smolagents](https://github.com/huggingface/smolagents) library, making the project available for use with MCP clients, such as AI assistants.

This is an early work-in-progress, has limited testing, and requires access to API's that will be replaced in the near future. For now, the following API keys are required to be set in the environment or in a `.env` file (see `.env.example`):

- OpenAI API Key: https://platform.openai.com/
- HuggingFace API Key: https://huggingface.co/
- SERP API Key: https://serpapi.com/

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
http://127.0.0.1:6020/sse
```

## Client Configuration

To use this MCP server in your setup, consider the following configuration:

### Stdio

```json
{
  "mcpServers": {
    "open-deep-research": {
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
    "{{ project_slug }}": {
      "command": "http://127.0.0.1:6020/sse",
      "args": []
    }
  }
}
```
