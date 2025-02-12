# Model Context Protocol (MCP)

## Overview

The Model Context Protocol (MCP) is an open protocol that enables seamless integration between LLM applications and external data sources and tools. Whether you're building an AI-powered IDE, enhancing a chat interface, or creating custom AI workflows, MCP provides a standardized way to connect LLMs with the context they need.

## This Folder, `ai-assist-content`

This folder contains files that may be useful to provide to any assistants that are helping with a project
that uses the Model Context Protocol (MCP).

### Files

- [mcp-llms-full.txt](./mcp-llms-full.txt): text version of the full documentation at https://modelcontextprotocol.io/
- [mcp-python-sdk-README.md](./mcp-python-sdk-README.md): README from the Python SDK at https://github.com/modelcontextprotocol/python-sdk
- [mcp-typescript-sdk-README.md](./mcp-typescript-sdk-README.md): README from the TypeScript SDK at https://github.com/modelcontextprotocol/typescript-sdk

## MPC Server Template

There is a `copier` template available to quickly generate a new MCP Server project. See the [MCP Server Template README](../mcp-server-template/README.md) for more information.

Users can generate a new MCP Server project from this template with the following command:

```bash
copier copy path/to/mcp-server-template path/to/destination
```

- last updated 2/12/25
