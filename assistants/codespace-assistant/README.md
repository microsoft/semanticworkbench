# Codespace Assistant

NOTE: DO NOT DEPLOY THIS ASSISTANT OUTSIDE OF CODESPACES (OR LOCAL, BUT THIS HAS NOT BEEN TESTED)

This assistant is designed to help with development within the Semantic Workbench repo in Codespaces, and is not intended for deployment to production environments.

The Codespace Assistant is designed to help developers work within the **Semantic Workbench** repository, particularly in **GitHub Codespaces** and **VS Code**. It provides tools, guidance, and integrations to simplify coding, debugging, and interacting with your projects. While optimized for Codespaces, it can also be used in local environments with some caveats.

---

## Key Features

- **MCP Server Integration**:
  - Provides access to tools like the MCP filesystem and VS Code servers by default.
  - Additional tools (e.g., Bing Search, OpenAI integrations) can be enabled via configuration.
- **Content Safety and Guardrails**:
  - Integrated with Azure OpenAI and OpenAI APIs for responsible AI usage.
  - Includes prompts for instruction, guidance, and guardrails.
- **Codespaces Optimization**:
  - Ready to run directly within Codespaces for a streamlined developer experience.
  - Also supports local setups, but **Windows users must use WSL** due to Linux dependencies.

---

## Prerequisites

### Codespaces Development
- Follow the guide in [Optimizing for Codespaces](../../.devcontainer/OPTIMIZING_FOR_CODESPACES.md) to set up your environment.
- **Using VS Code Desktop**:
  - Open the workspace: `/workspaces/semanticworkbench/semantic-workbench.code-workspace`.

### Local Development
- Refer to [Setup Developer Environment](../../docs/SETUP_DEV_ENVIRONMENT.md) for full instructions.
- **Windows Users**:
  - Must host the repository in **WSL (Windows Subsystem for Linux)** due to Linux library dependencies.

### Authentication
- You must authenticate with the Semantic Workbench using a **Microsoft or organizational account**. See [Workbench App Overview](../../docs/WORKBENCH_APP.md) for details.

---

## Setup Instructions

### Creating a Codespace
1. Go to the **Semantic Workbench** repository in GitHub.
2. Create a new Codespace.
3. Open the Codespace in **VS Code Desktop**.
   - Open the workspace file: `/workspaces/semanticworkbench/semantic-workbench.code-workspace`.

### Configure `.env` Variables
1. Navigate to the folder: `/assistants/codespace-assistant`.
2. Copy `.env.example` to `.env`.
3. Replace default values with your resource details for **Azure OpenAI** and **OpenAI** APIs.
   - **Azure**:
     - `ASSISTANT__AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint.
     - `ASSISTANT__AZURE_OPENAI_API_KEY`: Azure API key (use managed identities if possible).
     - `ASSISTANT__AZURE_CONTENT_SAFETY_ENDPOINT`: Azure Content Safety endpoint.
   - **OpenAI**:
     - `ASSISTANT__OPENAI_API_KEY`: API key for OpenAI.
     - `ASSISTANT__OPENAI_ORGANIZATION_ID`: Organization ID (optional).

### First Launch
1. Go to the **Debug** pane in VS Code.
2. Select `assistants: codespace-assistant (demo)`.
3. Start the assistant.
   - For more MCP servers, select `assistants: codespace-assistant (for dev)` (requires custom API keys).
4. Open your browser: [https://127.0.0.1:4000/](https://127.0.0.1:4000/).
   - Click "Advanced" > "Proceed to localhost" to bypass security warnings.
5. Create a conversation and add the assistant:
   - Provide a title.
   - Create a new assistant and select the Codespace Assistant service.
   - Start interacting with the assistant (e.g., ask questions about the repo).

---

## Extending Functionality

### Add Your Own Code
1. Open a terminal in VS Code.
2. Navigate to the `/workspaces` directory (default MCP filesystem server location).
3. Clone your repository or create a new folder.
   - Optionally, add it to the workspace using **File > Add Folder to Workspace**.

The assistant can now read, write, and edit your custom code.

---

## Additional MCP Servers (Advanced)

The `assistants: codespace-assistant (for dev)` debug configuration enables additional MCP servers not active by default. These servers can extend the assistant's functionality, but they require custom API keys to activate.

### Available MCP Servers

1. **Bing Search**:
   - **Command**: `http://127.0.0.1:6030/sse`
   - **Purpose**: Enables search capabilities via Bing.

2. **Open Deep Research**:
   - **Command**: `http://127.0.0.1:6020/sse`
   - **Purpose**: Facilitates deeper research workflows.

3. **Giphy**:
   - **Command**: `http://127.0.0.1:6000/sse`
   - **Purpose**: Fetches GIFs for use in conversations.

4. **Memory**:
   - **Command**: `npx @modelcontextprotocol/server-memory`
   - **Purpose**: Integrates a memory or knowledge graph system.

5. **Sequential Thinking**:
   - **Command**: `npx @modelcontextprotocol/server-sequential-thinking`
   - **Purpose**: Enables tools for sequential reasoning tasks.

### How to Enable Additional MCP Servers

1. Use the assistant configuration interface to enable these MCP servers directly. In the Semantic Workbench, navigate to the assistant's configuration panel, locate the MCP server settings, and toggle the desired servers on.
3. Check the `.env.example` file for each server's required API keys and configuration.
4. To enable a server, update the `.env` file with the necessary values and restart the assistant.

---

## Frequently Asked Questions (FAQs)

### Authentication and Access
- **Q**: How do I log into the Semantic Workbench?
  - **A**: Log in using your Microsoft or organizational account. See [Workbench App Overview](../../docs/WORKBENCH_APP.md).

### Common Errors
1. **Azure Content Safety Error**:
   - Issue: `Bearer token authentication is not permitted for non-HTTPS URLs.`
   - Solution: Configure the endpoint properly.
2. **Blank Screen on Startup**:
   - Check if pop-up blockers are preventing access.
3. **Connection Issues on 127.0.0.1**:
   - Ensure you're navigating to `https://127.0.0.1:4000/`.

### Enabling MCP Servers
- Navigate to the assistant configuration panel and enable or configure servers as needed.
- By default, the filesystem and VS Code servers are active. Others, like Bing Search or Giphy, can be enabled manually.

### Limits and Customization
1. **Maximum Steps Reached**:
   - Expand the assistant's steps by updating the `Maximum Steps` setting in the assistant configuration.
2. **Folder Not Found**:
   - Verify the path is under `/workspaces`. Adjust permissions if needed.

---

## Additional Resources

- [Optimizing for Codespaces](../../.devcontainer/OPTIMIZING_FOR_CODESPACES.md)
- [Workbench App Overview](../../docs/WORKBENCH_APP.md)
- [Setup Developer Environment](../../docs/SETUP_DEV_ENVIRONMENT.md)
- [Assistant Development Guide](../../docs/ASSISTANT_DEVELOPMENT_GUIDE.md)

For issues, see the [Semantic Workbench README](../../README.md) or raise a question in the repository.