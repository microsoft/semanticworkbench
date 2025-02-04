# MCP Coder Server

## Overview

This project implements a Model Context Protocol (MCP) server designed to provide coding-specific tools and functionalities. The server aims to assist in performing common development tasks directly from an assistant platform.

## Features

- **Coding Tools**:

  - `code_checker`: A tool that runs linting (using Ruff) and type-checking (using mypy) on provided files, reporting aggregated issues for review and iteration.

- **Code Analysis**:
  - The tool currently works file-by-file but can be enhanced to recursively check directories upon receiving a directory path.
  - It mimics the behavior of VSCode’s Problems panel by validating Python code quality and correctness based on the project’s linters and type-checkers.

## Plans and Objectives

### Immediate Enhancements

1. **Code Checker Tool Enhancements**:

   - Extend the `code_checker` tool to support recursive analysis of a directory.
   - Aggregate diagnostics for each Python file, providing detailed outputs clearly associated with file paths.

2. **Output Improvements**:
   - Tune tool outputs to ensure greater alignment with behaviors and outputs commonly seen in VSCode’s Problems panel, for seamless integration into workflows.

### Long-Term Goals

1. **Language Server Integration Option**:

   - Investigate attaching or embedding a Python language server (e.g., Pyright/Pylance or one via pygls).
   - This would enable real-time, incremental diagnostics during file edits and dynamic notifications similar to VSCode.

2. **Usability Enhancements**:
   - Consider feedback loops and iterative workflows where diagnostics lead to actionable suggestions for fixes.

## Development Principles

- **Modularity and Conciseness:** Each code file should not exceed one page in length, ensuring concise and focused code.
- **Semantic Names:** Use meaningful names for functions and modules to enhance understanding and maintainability.
- **Organized Structure:** Maintain a well-organized structure, breaking down functionality into clear and manageable components.

## Project Structure

```
/mcp-server-coder
│
├── README.md
├── server
│   ├── __init__.py
│   ├── main.py
│   └── [Other potential modules]
```

## High-Level Plan for MCP Coder Server

**Objective**: Enhance the coding environment by providing tools for code analysis, testing, and more, complementing existing general-purpose servers like the filesystem server.

### Priority 1: Code Analysis Tools

1. **Linting and Type-Checking**

   - **Purpose**: Identify syntax errors, stylistic standards, and type safety issues in code.
   - **Implementation Options**:
     - **Separate Tools**: Provide dedicated tools for linting and type-checking.
     - **Unified Tool**: Develop a comprehensive "code-checker" tool that aggregates multiple checks.

2. **Output Handling**
   - Ensure the output from these checks is returned in a structured format.
   - Allow the calling assistant to assess the results and decide subsequent actions.

### Priority 2: Code Testing Tools

1. **Test Execution**

   - **Purpose**: Run unit tests or integration tests on the codebase.
   - **Interaction with Filesystem Tools**: Leverage existing tools for file operations needed during test preparation and execution.

2. **Output Management**
   - Capture test results and return detailed reports.
   - Enable the assistant to verify results, address test failures, and iterate if necessary.

### Considerations for Both Toolsets

- **Environment Awareness**: Tools must consider the coding environment (e.g., dependencies, configurations) to provide accurate assessments.
- **Iterative Integration**: Facilitate a workflow where the assistant can continue tasks based on tool outputs (revision, re-running, etc.).
- **User Engagement**: Implement features for user fallback if automated processes can't resolve issues.

## Setup and Running

### Prerequisites

- Ensure Python 3.11 or higher is installed.

### Setup and Installation

To set up the project, simply run:

```bash
make
```

This will handle the virtual environment creation and install necessary dependencies.

### Running the Server

You can run the MCP Coder Server in two modes: **Stdio** or **SSE**.

#### Running with Stdio Transport

To run the server using stdio (default transport):

```bash
python server/main.py --transport stdio
```

This mode operates over input/output streams and does not open a network port.

#### Running with SSE Transport

To run the server using SSE (Server-Sent Events) transport:

```bash
python server/main.py --transport sse --port 6010
```

When running in SSE mode, the server will be available at the following URL:

```
http://127.0.0.1:6010/sse
```

## Client Configuration

To use this MCP server in your setup, consider the following configuration:

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

Ensure that required environment variables are set in your environment so that the server can function correctly.
