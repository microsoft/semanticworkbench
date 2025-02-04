# ASSISTANT_BOOTSTRAP.md: AI Assistant Onboarding and Ramp-Up Guide

## 1. Introduction

Welcome, future AI collaborator!

This document is your complete bootstrap guide for the MCP Coder Server project. It is designed so that you can autonomously ramp up on all aspects of the project without further human intervention. Your primary goals are to understand the project’s context, review all the relevant files, and then proceed with the next development steps as outlined below.

**Instructions:**
- Read this document in its entirety.
- Follow the step-by-step operations described in the “Onboarding Steps” section.
- Use your integrated file system tools (or available commands like `list_directory` and `read_file`) to explore directories and load file content.
- Once you have gathered all context, summarize your understanding and propose next steps based on the project’s current state and future plans.

---

## 2. Project Background and Context

### 2.1 The MCP Coder Server Project

- **Purpose:**
  The MCP Coder Server is an implementation of the Model Context Protocol (MCP) server designed specifically to provide coding-related tools and functionalities. Its current primary tool, `code_checker`, runs linting (via Ruff) and type-checking (via Mypy) on Python files to report diagnostic issues—mimicking VSCode's Problems panel.

- **Key Goals:**
  - Automate the analysis of code quality and type correctness.
  - Serve as a supplement to general-purpose MCP servers (e.g., the filesystem server) by focusing on coding-specific tasks.
  - Provide a foundation to eventually integrate real-time diagnostics through a language server if needed.

### 2.2 The MCP Ecosystem

- **MCP (Model Context Protocol):**
  A protocol designed to connect language models with external tools and data sources. Familiarize yourself with the MCP context by reviewing our documentation files located in the `ai-assist-content` directory.

### 2.3 Related Projects for Reference

- **MCP Context Documentation:**
  Located at `/workspaces/semanticworkbench/mcp-servers/ai-assist-content` (files such as `README.md`, `mcp-llms-full.txt`, and `mcp-python-sdk-README.md`). These files explain the MCP protocol and provide guidelines for building MCP servers.

- **Reference Implementation – MCP Server Giphy:**
  Located at `/workspaces/semanticworkbench/mcp-servers/mcp-server-giphy`. This project serves as a reference for our code patterns and configurations in the MCP server ecosystem.

---

## 3. Onboarding Steps and File Exploration

Your task is to methodically gather context from all relevant parts of the project. Follow these steps:

### Step 1: Load MCP Context Documentation
- **Action:**  
  Use your directory listing tool to list all files in:
  
  `/workspaces/semanticworkbench/mcp-servers/ai-assist-content`

- **Then:**  
  Read the following files:
  - `README.md`
  - `mcp-llms-full.txt`
  - `mcp-python-sdk-README.md`

These files provide the conceptual framework for MCP and contextual guidelines.

---

### Step 2: Examine the Reference Implementation
- **Action:**  
  List all files in the MCP Server Giphy project:
  
  `/workspaces/semanticworkbench/mcp-servers/mcp-server-giphy`

- **Then:**  
  Specifically review the files in its `server` subdirectory (e.g., `main.py`, `giphy_search.py`) and high-level configuration files (like `pyproject.toml` and `.vscode` settings).

This will help you understand best practices and reference design patterns used in our MCP projects.

---

### Step 3: Explore the MCP Coder Server Project
- **Action:**  
  List all files in:
  
  `/workspaces/semanticworkbench/mcp-servers/mcp-server-coder`

- **Then:**  
  Recursively read the contents of key files and directories, including but not limited to:
  - `README.md`
  - `pyproject.toml`
  - `.vscode` (and all its contents)
  - `server/main.py`
  - `server/code_checker.py`

Ensure you understand the project structure and how the tool interfaces work.

---

### Step 4: Validate and Summarize Project Diagnostics
- **Action:**  
  Test the `code_checker` tool on sample files (for example, running it on a well-known file such as `server/code_checker.py`) to understand how diagnostics are aggregated.

- **Then:**  
  Summarize your findings, noting any issues, and propose any necessary next steps for enhancements.

---

## 4. Next Steps for Development and Enhancement

Once you have assimilated the project context:
1. **Immediate Tasks:**
   - Enhance the `code_checker` tool to support recursive (directory-level) analysis.
   - Assess the aggregated diagnostic outputs and propose improvements for output formatting.
   
2. **Future Work:**
   - Explore integrating a lightweight language server (using, for example, pygls) to provide continuous, real-time diagnostics similar to VSCode’s built-in support.
   - Refine client configurations for seamless integration with our MCP ecosystem.

3. **Reporting:**
   - Summarize your complete understanding of the project and generate a detailed plan for subsequent development tasks.

---

## 5. How to Proceed

1. **Read this document completely and follow the instructions it contains.**
2. **Execute the onboarding steps in the order provided:**
   - Start by listing and reading the MCP context files in `/workspaces/semanticworkbench/mcp-servers/ai-assist-content`.
   - Next, review the reference implementation in `/workspaces/semanticworkbench/mcp-servers/mcp-server-giphy`.
   - Then, recursively read key files in the MCP Coder Server project.
3. **Document your findings and propose next steps** for further development.
4. **Finally, report back your complete understanding** and a detailed plan for subsequent enhancements.

Good luck with your onboarding! Once you have processed all this information, you will be fully ramped up on the project and ready to pursue further development tasks autonomously.
