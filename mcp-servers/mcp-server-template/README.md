# 📦 Copier Template for MCP Server Projects

This directory contains a **Copier template** that can be used to generate new MCP Server projects quickly.

## How to Use This Template

### **Generate a New MCP Server Project from This Template**

Run the following command from anywhere:

```bash
uvx copier copy path/to/template path/to/destination
```

🔹 **`path/to/template`** → Path to the same directory that this README.md is in.
🔹 **`path/to/destination`** → Replace with the directory where you want the new project.

**Example:**

```bash
# from the {repo_root}/mcp-server directory
uvx copier copy mcp-server-template .
```

This will prompt you to fill in project details and generate a new project inside `{repo_root}/mcp-servers/{your_mcp_server}`.

---

## Updating an Existing Project

If you need to apply updates from this template to an existing project, use:

```bash
uvx copier update path/to/existing_project
```

This will merge the latest template changes into your project while preserving custom modifications.
