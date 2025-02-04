# MCP Coder Server

## Overview

This project implements a Model Context Protocol (MCP) server designed to provide coding-specific tools and functionalities. The server assists by automating code quality checks, type-checking, and eventually testing—mimicking the behavior of VSCode’s Problems panel for diagnosing Python code issues.

## Features

- **Coding Tools**:

  - `code_checker`: A tool that runs linting (using Ruff) and type-checking (using Mypy) on provided files, aggregating diagnostic messages for review and iteration.

- **Code Analysis**:
  - Currently, the tool operates file-by-file but is designed to be enhanced in the future to support recursive analysis of directories.
  - It aggregates diagnostic messages in a structured format so that issues are clearly associated with the corresponding file paths.

## Plans and Objectives

### Immediate Enhancements

1. **Code Checker Tool Enhancements**:
   - Extend the `code_checker` tool to support recursive directory analysis, scanning all `.py` files and aggregating their diagnostics.
2. **Output Improvements**:
   - Refine the output format so that it aligns more closely with the standard diagnostic views in VSCode’s Problems panel.

### Long-Term Goals

1. **Language Server Integration Option**:
   - Investigate integrating a Python language server (e.g., Pyright/Pylance or one via pygls) into the MCP server. This would enable real-time, incremental diagnostics and notifications, matching the native experience in tools like VSCode.
2. **Usability Enhancements**:
   - Develop feedback loops and iterative workflows where diagnostic outputs lead to actionable suggestions for code fixes.

## Development Principles

- **Modularity and Conciseness:** Each code file should remain focused and concise.
- **Semantic Naming:** Use clear, meaningful names for functions and modules.
- **Organized Structure:** Ensure the project is structured in a maintainable manner with clear separation of concerns.

## Project Structure

```
/mcp-server-coder
│
├── README.md                # This file – Documentation for the project
├── pyproject.toml           # Dependency and configuration management
├── .vscode/                 # VSCode workspace settings and debugging configurations
└── server/                  # Core server code
    ├── __init__.py
    ├── main.py            # The entry point; registers MCP tools
    └── code_checker.py    # Implementation of the unified code_checker tool
```

## Setup and Installation

To set up the project, navigate to the project root (or open it in your Codespace) and run:

```bash
make
```

This command will create the virtual environment using the `uv` tool and install all necessary dependencies as defined in `pyproject.toml`.

## Running the Server

You can run the MCP Coder Server in two modes: **Stdio** or **SSE**.

### Running with Stdio Transport

To run the server using stdio (default mode):

```bash
python server/main.py --transport stdio
```

_This mode uses standard input/output streams and does not expose a network port._

### Running with SSE Transport

To run the server using SSE (Server-Sent Events) transport, execute:

```bash
python server/main.py --transport sse --port 6010
```

In this mode, the server will be available at the following URL:

```
http://127.0.0.1:6010/sse
```

## Client Configuration

To integrate this MCP server within your environment, you can use one of the following configuration examples:

### UV - Local Files

```json
{
  "mcpServers": {
    "coder-server": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/project/mcp-server-coder",
        "run",
        "server/main.py"
      ]
    }
  }
}
```

### SSE

```json
{
  "mcpServers": {
    "coder-server": {
      "command": "http://127.0.0.1:6010/sse",
      "args": []
    }
  }
}
```

Ensure that the required environment variables (if any) are properly set for the server to operate correctly.
