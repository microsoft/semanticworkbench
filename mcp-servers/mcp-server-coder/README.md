# MCP Coder Server

## Overview

This project implements a Model Context Protocol (MCP) server designed to provide coding-specific tools and functionalities. The server aims to assist in performing common development tasks directly from an assistant platform.

## Features

- **TODO: Coding Tools**: [Describe specific coding tools once they are implemented.]
- **TODO: Code Analysis**: [Details for any code analysis features.]

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

Use the VSCode launch configuration, or to run manually:

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
