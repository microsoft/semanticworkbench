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
  ```
  /workspaces/semanticworkbench/mcp-servers/ai-assist-content
  ```
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
  ```
  /workspaces/semanticworkbench/mcp-servers/mcp-server-giphy
  ```
- **Then:**
  Specifically review the files in its `server` subdirectory (e.g., `main.py`, `giphy_search.py`, etc.) and high-level configuration files (like `pyproject.toml` and `.vscode` settings).

This will help you understand best practices and reference design patterns used in our MCP projects.

---

### Step 3: Explore the MCP Coder Server Project

- **Action:**
  List all files in the MCP Coder Server directory:
  ```
  /workspaces/semanticworkbench/mcp-servers/mcp-server-coder
  ```
- **Then:**
  Recursively read the contents of key files and directories, including but not limited to:
  - **README.md:** Provides an overview and planning details.
  - **pyproject.toml:** Shows dependency management and configuration.
  - **.vscode/**: Contains VSCode-specific settings and debugging configurations.
  - **server/main.py:** The entry point and tool registration.
  - **server/code_checker.py:** The current implementation of the code_checker tool.

These files represent the core of the project. Ensure that you fully understand the structure and how the tool interfaces work.

---

### Step 4: Validate and Summarize Project Diagnostics

- **Action:**
  Test the `code_checker` tool on various files (for example, run it on itself) to understand how diagnostics are aggregated.
  - Use the tool call function in your model completion calls.
- **Then:**
  Capture and note any diagnostic outputs (both linting and type checking) to inform potential enhancements.

---

## 4. Next Steps for Development and Enhancement

Once you have assimilated the project context:

1. **Immediate Tasks:**

   - Consider extending the `code_checker` tool to support recursive (directory-level) analysis.
   - Assess the diagnostic outputs and propose improvements in output formatting.

2. **Future Work:**

   - Explore integrating a lightweight language server for continuous, real-time diagnostics. Investigate frameworks like pygls for this purpose.
   - Refine client configurations to ensure seamless integration with our existing MCP ecosystem.

3. **Reporting:**
   - Summarize your understanding and propose a detailed plan for moving forward. Include any observations, potential issues, and priorities for further work.

---

## 5. How to Proceed

1. **Read This Document Completely:**
   Ensure you understand every section and the instructions provided.

2. **Execute the Onboarding Steps in Order:**
   Start by listing and reading the MCP context files, then move to the reference implementations, and finally, review our own project files.

3. **Document Your Findings:**
   As you progress, keep a log (or update this document) of any insights, anomalies, or next steps you identify.

4. **Finalize Onboarding:**
   Once you have a complete understanding, generate a summary report detailing the current project state and your proposed next steps.

---

This document should serve as your central bootstrap guide to effectively ramp up on the MCP Coder Server project. Follow the instructions carefully, use the provided tools to gather context, and then determine the best path forward.

Good luck with your onboarding, and let’s build something great!
