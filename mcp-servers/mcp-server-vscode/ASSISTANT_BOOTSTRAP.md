# ASSISTANT_BOOTSTRAP.md: AI Assistant Onboarding and Ramp-Up Guide

## 1. Introduction

Welcome to the VSCode MCP Server project! This VSCode extension serves as an MCP (Model Context Protocol) server integrated directly within VSCode. Its primary function is to expose a coding diagnostic tool (the `code_checker`) that aggregates diagnostic messages (similar to those shown in VSCode’s Problems panel) and makes them accessible to an external AI assistant via Server-Sent Events (SSE).

**Instructions:**

-   Read this document in its entirety.
-   Follow the step-by-step operations described in the “Onboarding Steps” section.
-   Use your integrated file system tools (or available commands like `list_directory` and `read_file`) to explore directories and load file content.
-   Once you have gathered all context, summarize your understanding and propose next steps based on the project’s current state and future plans.

## 2. Project Overview

The VSCode MCP Server is designed to:

-   **Automatically Start:** Activate on VSCode startup (using `"activationEvents": ["*"]` in package.json) so that the MCP server runs without manual intervention.
-   **Expose an MCP Server:** Instantiate an MCP server using the TypeScript SDK (`@modelcontextprotocol/sdk`) within the extension.
-   **Provide Diagnostic Tools:** Register a `code_checker` tool that retrieves diagnostics (errors/warnings) from VSCode's built-in language services, filtering out files without issues.
-   **Communicate via SSE:** Run an Express-based HTTP server that listens on port 6010, providing a GET `/sse` endpoint (to establish a long-lived SSE connection) and a POST `/messages` endpoint for incoming MCP messages.
-   **Log Activity:** All activity, including server startup, SSE connection status, and message handling events, is logged to an output channel named **"MCP Server Logs"**—this aids in debugging and ensures transparency of operations.

---

### 2.2 The MCP Ecosystem

-   **MCP (Model Context Protocol):**
    A protocol designed to connect language models with external tools and data sources. Familiarize yourself with the MCP context by reviewing our documentation files located in the `ai-assist-content` directory.

### 2.3 Related Projects for Reference

-   **MCP Context Documentation:**
    Located at `/workspaces/semanticworkbench/mcp-servers/ai-assist-content` (files such as `README.md`, `mcp-llms-full.txt`, and `mcp-python-sdk-README.md`). These files explain the MCP protocol and provide guidelines for building MCP servers.

-   **Reference Implementation – MCP Server Giphy:**
    Located at `/workspaces/semanticworkbench/mcp-servers/mcp-server-giphy`. This project serves as a reference for our code patterns and configurations in the MCP server ecosystem.

---

## 3. Onboarding Steps and File Exploration

Your task is to methodically gather context from all relevant parts of the project. Follow these steps:

### Step 1: Load MCP Context Documentation

-   **Action:**
    Use your directory listing tool to list all files in:

    `/workspaces/semanticworkbench/mcp-servers/ai-assist-content`

-   **Then:**
    Read the following files:
    -   `README.md`
    -   `mcp-llms-full.txt`
    -   `mcp-python-sdk-README.md`

These files provide the conceptual framework for MCP and contextual guidelines.

---

### Step 2: Examine the Reference Implementation

-   **Action:**
    List all files in the MCP Server Giphy project:

    `/workspaces/semanticworkbench/mcp-servers/mcp-server-giphy`

-   **Then:**
    Specifically review the files in its `server` subdirectory (e.g., `main.py`, `giphy_search.py`) and high-level configuration files (like `pyproject.toml` and `.vscode` settings).

This will help you understand best practices and reference design patterns used in our MCP projects.

---

### Step 3: Explore the VSCode MCP Server VSCode Extension Project

-   **Action:**
    List all files in:

    `/workspaces/semanticworkbench/mcp-servers/mcp-server-vscode`

-   **Then:**
    Recursively read the contents of key files and directories, including but not limited to:
    -   `README.md`
    -   `package.json`
    -   `.vscode` (and all its contents)
    -   `src/extension.ts`

Ensure you understand the project structure and how the tool interfaces work.

---

## 4. Next Steps for Development and Enhancement

Once you have assimilated the project context:

1. **Immediate Tasks:**
    - Ask user to have you test the tool and verify it works as expected.
    - Assess the aggregated diagnostic outputs and propose improvements for output formatting.
    - Add support at both the server config args and the client side for filtering diagnostics by severity (e.g., only show errors, only show warnings, ignore "hint" diagnostics).
2. **Future Work:**

    - Consider what other capabilities should be added to the `code_checker` tool or the MCP server itself.

3. **Reporting:**
    - Summarize your complete understanding of the project and generate a detailed plan for subsequent development tasks.

---

## 5. How to Proceed

1. **Read this document completely and follow the instructions it contains.**
2. **Execute the onboarding steps in the order provided:**
    - Start by listing and reading the MCP context files in `/workspaces/semanticworkbench/mcp-servers/ai-assist-content`.
    - Next, review the reference implementation in `/workspaces/semanticworkbench/mcp-servers/mcp-server-giphy`.
    - Then, recursively read key files in the VSCode MCP Server project.
3. **Document your findings and propose next steps** for further development.
4. **Finally, report back your complete understanding** and a detailed plan for subsequent enhancements.

Good luck with your onboarding! Once you have processed all this information, you will be fully ramped up on the project and ready to pursue further development tasks autonomously.
