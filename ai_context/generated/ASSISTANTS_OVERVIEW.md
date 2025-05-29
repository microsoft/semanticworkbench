# assistants/Makefile

[collect-files]

**Search:** ['assistants/Makefile']
**Exclude:** ['.venv', 'node_modules', '*.lock', '.git', '__pycache__', '*.pyc', '*.ruff_cache', 'logs', 'output']
**Include:** ['assistants/*/README.md', 'assistants/*/pyproject.toml']
**Date:** 5/29/2025, 11:45:28 AM
**Files:** 17

=== File: assistants/Makefile ===
repo_root = $(shell git rev-parse --show-toplevel)
include $(repo_root)/tools/makefiles/recursive.mk


=== File: assistants/codespace-assistant/README.md ===
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

=== File: assistants/codespace-assistant/pyproject.toml ===
[project]
name = "codespace-assistant"
version = "0.1.0"
description = "A python Semantic Workbench OpenAI assistant for assisting with development in codespaces."
authors = [{ name = "Semantic Workbench Team" }]
readme = "README.md"
requires-python = ">=3.11,<3.13"
dependencies = [
    "assistant-drive>=0.1.0",
    "assistant-extensions[attachments, mcp]>=0.1.0",
    "mcp-extensions[openai]>=0.1.0",
    "content-safety>=0.1.0",
    "deepmerge>=2.0",
    "openai>=1.61.0",
    "openai-client>=0.1.0",
    "tiktoken>=0.8.0",
]

[tool.hatch.build.targets.wheel]
packages = ["assistant"]

[tool.uv]
package = true

[tool.uv.sources]
anthropic-client = { path = "../../libraries/python/anthropic-client", editable = true }
assistant-drive = { path = "../../libraries/python/assistant-drive", editable = true }
assistant-extensions = { path = "../../libraries/python/assistant-extensions", editable = true }
mcp-extensions = { path = "../../libraries/python/mcp-extensions", editable = true }
content-safety = { path = "../../libraries/python/content-safety/", editable = true }
openai-client = { path = "../../libraries/python/openai-client", editable = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[dependency-groups]
dev = ["pyright>=1.1.389"]


=== File: assistants/document-assistant/README.md ===
# Document Assistant

NOTE: DO NOT DEPLOY THIS ASSISTANT OUTSIDE OF CODESPACES (OR LOCAL, BUT THIS HAS NOT BEEN TESTED)

This assistant is designed to help with development within the Semantic Workbench repo in Codespaces, and is not intended for deployment to production environments.

The Document Assistant is an AI assistant focused on being easy to use for everyone with a core feature being
reliable document creation and editing, grounded in all of your context across files and the conversation.

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
2. Check the `.env.example` file for each server's required API keys and configuration.
3. To enable a server, update the `.env` file with the necessary values and restart the assistant.

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


=== File: assistants/document-assistant/pyproject.toml ===
[project]
name = "document-assistant"
version = "0.1.0"
description = "A python Semantic Workbench OpenAI assistant for document editing."
authors = [{ name = "Semantic Workbench Team" }]
readme = "README.md"
requires-python = ">=3.11,<3.13"
dependencies = [
    "assistant-drive>=0.1.0",
    "assistant-extensions[attachments, mcp]>=0.1.0",
    "mcp-extensions[openai]>=0.1.0",
    "content-safety>=0.1.0",
    "deepmerge>=2.0",
    "markitdown[docx,outlook,pptx,xlsx]==0.1.1",
    "openai>=1.61.0",
    "openai-client>=0.1.0",
    "pdfplumber>=0.11.2",
    "pendulum>=3.1,<4.0",
    "python-liquid>=2.0,<3.0",
    "tiktoken>=0.9.0",
]

[tool.hatch.build.targets.wheel]
packages = ["assistant"]

[tool.uv]
package = true

[tool.uv.sources]
anthropic-client = { path = "../../libraries/python/anthropic-client", editable = true }
assistant-drive = { path = "../../libraries/python/assistant-drive", editable = true }
assistant-extensions = { path = "../../libraries/python/assistant-extensions", editable = true }
mcp-extensions = { path = "../../libraries/python/mcp-extensions", editable = true }
content-safety = { path = "../../libraries/python/content-safety/", editable = true }
openai-client = { path = "../../libraries/python/openai-client", editable = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[dependency-groups]
dev = ["pyright>=1.1.389", "pytest", "pytest-asyncio"]

[tool.pytest.ini_options]
asyncio_default_fixture_loop_scope = "function"
asyncio_mode = "auto"


=== File: assistants/explorer-assistant/README.md ===
# Using Semantic Workbench with python assistants

This project provides an assistant to help explore assistant ideas and capabilities, leveraging OpenAI or Azure OpenAI (or any OpenAI compatible service), allowing to use **Semantic Workbench** to test it.

## Responsible AI

The chatbot includes some important best practices for AI development, such as:

- **System prompt safety**, ie a set of LLM guardrails to protect users. As a developer you should understand how these
  guardrails work in your scenarios, and how to change them if needed. The system prompt and the prompt safety
  guardrails are split in two to help with testing. When talking to LLM models, prompt safety is injected before the
  system prompt.
  - See https://learn.microsoft.com/azure/ai-services/openai/concepts/system-message for more details
    about protecting application and users in different scenarios.
- **Content moderation**, via [Azure AI Content Safety](https://azure.microsoft.com/products/ai-services/ai-content-safety)
  or [OpenAI Content Moderation](https://platform.openai.com/docs/guides/moderation).

See the [Responsible AI FAQ](../../RESPONSIBLE_AI_FAQ.md) for more information.

# Suggested Development Environment

- Use GitHub Codespaces for a quick, turn-key dev environment: [/.devcontainer/README.md](../../.devcontainer/README.md)
- VS Code is recommended for development

## Pre-requisites

- Set up your dev environment
  - SUGGESTED: Use GitHub Codespaces for a quick, easy, and consistent dev
    environment: [/.devcontainer/README.md](../../.devcontainer/README.md)
  - ALTERNATIVE: Local setup following the [main README](../../README.md#local-development-environment)
- Set up and verify that the workbench app and service are running using the [semantic-workbench.code-workspace](../../semantic-workbench.code-workspace)
- If using Azure OpenAI, set up an Azure account and create a Content Safety resource
  - See [Azure AI Content Safety](https://azure.microsoft.com/products/ai-services/ai-content-safety) for more information
  - Copy the `.env.example` to `.env` and update the `ASSISTANT__AZURE_CONTENT_SAFETY_ENDPOINT` value with the endpoint of your Azure Content Safety resource
  - From VS Code > `Terminal`, run `az login` to authenticate with Azure prior to starting the assistant

## Steps

- Use VS Code > `Run and Debug` (ctrl/cmd+shift+d) > `semantic-workbench` to start the app and service from this workspace
- Use VS Code > `Run and Debug` (ctrl/cmd+shift+d) > `launch assistant` to start the assistant.
- If running in a devcontainer, follow the instructions in [.devcontainer/POST_SETUP_README.md](../../.devcontainer/POST_SETUP_README.md#start-the-app-and-service) for any additional steps.
- Return to the workbench app to interact with the assistant
- Add a new assistant from the main menu of the app, choose the assistant name as defined by the `service_name` in [chat.py](./explorer_assistant/chat.py)
- Click the newly created assistant to configure and interact with it

## Starting the example from CLI

If you're not using VS Code and/or Codespaces, you can also work from the
command line, using `uv`:

```
cd <PATH TO THIS FOLDER>

uv run start-assistant
```

## Create your own assistant

Copy the contents of this folder to your project.

- The paths are already set if you put in the same repo root and relative path of `/<your_projects>/<your_assistant_name>`
- If placed in a different location, update the references in the `pyproject.toml` to point to the appropriate locations for the `semantic-workbench-*` packages

## From Development to Production

It's important to highlight how Semantic Workbench is a development tool, and it's not designed to host agents in
a production environment. The workbench helps with testing and debugging, in a development and isolated environment, usually your localhost.

The core of your assistant/AI application, e.g. how it reacts to users, how it invokes tools, how it stores data, can be
developed with any framework, such as Semantic Kernel, Langchain, OpenAI assistants, etc. That is typically the code
you will add to `chat.py`.

**Semantic Workbench is not a framework**. Dependencies on `semantic-workbench-assistant` package are used only to test and debug your code in Semantic Workbench. **When an assistant is fully developed and ready for production, configurable settings should be hard coded, dependencies on `semantic-workbench-assistant` and similar should be removed**.


=== File: assistants/explorer-assistant/pyproject.toml ===
[project]
name = "explorer-assistant"
version = "0.1.0"
description = "A python Semantic Workbench OpenAI assistant for exploring capabilities."
authors = [{ name = "Semantic Workbench Team" }]
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "anthropic>=0.40.0",
    "anthropic-client>=0.1.0",
    "assistant-drive>=0.1.0",
    "assistant-extensions[attachments]>=0.1.0",
    "content-safety>=0.1.0",
    "deepmerge>=2.0",
    "html2docx>=1.6.0",
    "markdown>=3.6",
    "openai>=1.61.0",
    "openai-client>=0.1.0",
]

[tool.hatch.build.targets.wheel]
packages = ["assistant"]

[tool.uv]
package = true

[tool.uv.sources]
anthropic-client = { path = "../../libraries/python/anthropic-client", editable = true }
assistant-drive = { path = "../../libraries/python/assistant-drive", editable = true }
assistant-extensions = { path = "../../libraries/python/assistant-extensions", editable = true }
content-safety = { path = "../../libraries/python/content-safety/", editable = true }
openai-client = { path = "../../libraries/python/openai-client", editable = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[dependency-groups]
dev = ["pyright>=1.1.389"]


=== File: assistants/guided-conversation-assistant/README.md ===
# Using Semantic Workbench with python assistants

This project provides an assistant to demonstrate how to guide a user towards a goal, leveraging the [guided-conversation library](../../libraries/python/guided-conversation/), which is a modified copy of the [guided-conversation](https://github.com/microsoft/semantic-kernel/tree/main/python/samples/demos/guided_conversations) library from the [Semantic Kernel](https://github.com/microsoft/semantic-kernel) repository.

## Responsible AI

The chatbot includes some important best practices for AI development, such as:

- **System prompt safety**, ie a set of LLM guardrails to protect users. As a developer you should understand how these
  guardrails work in your scenarios, and how to change them if needed. The system prompt and the prompt safety
  guardrails are split in two to help with testing. When talking to LLM models, prompt safety is injected before the
  system prompt.
  - See https://learn.microsoft.com/azure/ai-services/openai/concepts/system-message for more details
    about protecting application and users in different scenarios.
- **Content moderation**, via [Azure AI Content Safety](https://azure.microsoft.com/products/ai-services/ai-content-safety)
  or [OpenAI Content Moderation](https://platform.openai.com/docs/guides/moderation).

See the [Responsible AI FAQ](../../RESPONSIBLE_AI_FAQ.md) for more information.

# Suggested Development Environment

- Use GitHub Codespaces for a quick, turn-key dev environment: [/.devcontainer/README.md](../../.devcontainer/README.md)
- VS Code is recommended for development

## Pre-requisites

- Set up your dev environment
  - SUGGESTED: Use GitHub Codespaces for a quick, easy, and consistent dev
    environment: [/.devcontainer/README.md](../../.devcontainer/README.md)
  - ALTERNATIVE: Local setup following the [main README](../../README.md#local-development-environment)
- Set up and verify that the workbench app and service are running using the [semantic-workbench.code-workspace](../../semantic-workbench.code-workspace)
- If using Azure OpenAI, set up an Azure account and create a Content Safety resource
  - See [Azure AI Content Safety](https://azure.microsoft.com/products/ai-services/ai-content-safety) for more information
  - Copy the `.env.example` to `.env` and update the `ASSISTANT__AZURE_CONTENT_SAFETY_ENDPOINT` value with the endpoint of your Azure Content Safety resource
  - From VS Code > `Terminal`, run `az login` to authenticate with Azure prior to starting the assistant

## Steps

- Use VS Code > `Run and Debug` (ctrl/cmd+shift+d) > `semantic-workbench` to start the app and service from this workspace
- Use VS Code > `Run and Debug` (ctrl/cmd+shift+d) > `launch assistant` to start the assistant.
- If running in a devcontainer, follow the instructions in [.devcontainer/POST_SETUP_README.md](../../.devcontainer/POST_SETUP_README.md#start-the-app-and-service) for any additional steps.
- Return to the workbench app to interact with the assistant
- Add a new assistant from the main menu of the app, choose the assistant name as defined by the `service_name` in [chat.py](./assistant/chat.py)
- Click the newly created assistant to configure and interact with it

## Starting the example from CLI

If you're not using VS Code and/or Codespaces, you can also work from the
command line, using `uv`:

```
cd <PATH TO THIS FOLDER>

uv run start-assistant
```

## Create your own assistant

Copy the contents of this folder to your project.

- The paths are already set if you put in the same repo root and relative path of `/<your_projects>/<your_assistant_name>`
- If placed in a different location, update the references in the `pyproject.toml` to point to the appropriate locations for the `semantic-workbench-*` packages

## From Development to Production

It's important to highlight how Semantic Workbench is a development tool, and it's not designed to host agents in
a production environment. The workbench helps with testing and debugging, in a development and isolated environment, usually your localhost.

The core of your assistant/AI application, e.g. how it reacts to users, how it invokes tools, how it stores data, can be
developed with any framework, such as Semantic Kernel, Langchain, OpenAI assistants, etc. That is typically the code
you will add to `chat.py`.

**Semantic Workbench is not a framework**. Dependencies on `semantic-workbench-assistant` package are used only to test and debug your code in Semantic Workbench. **When an assistant is fully developed and ready for production, configurable settings should be hard coded, dependencies on `semantic-workbench-assistant` and similar should be removed**.


=== File: assistants/guided-conversation-assistant/pyproject.toml ===
[project]
name = "assistant"
version = "0.1.0"
description = "An assistant that will guide users through a conversation towards a specific goal."
authors = [{ name = "Semantic Workbench Team" }]
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "deepmerge>=2.0",
    "docx2txt>=0.8",
    "html2docx>=1.6.0",
    "markdown>=3.6",
    "openai>=1.61.0",
    "pdfplumber>=0.11.2",
    "tiktoken>=0.8.0",
    "semantic-workbench-assistant>=0.1.0",
    "content-safety>=0.1.0",
    "semantic-kernel>=1.11.0",
    "guided-conversation>=0.1.0",
    "openai-client>=0.1.0",
]

[tool.uv]
package = true

[tool.uv.sources]
semantic-workbench-assistant = { path = "../../libraries/python/semantic-workbench-assistant", editable = true }
content-safety = { path = "../../libraries/python/content-safety/", editable = true }
guided-conversation = { path = "../../libraries/python/guided-conversation", editable = true }
openai-client = { path = "../../libraries/python/openai-client", editable = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[dependency-groups]
dev = ["pyright>=1.1.389"]

[tool.pyright]
exclude = ["**/.venv", "**/.data", "**/__pycache__"]


=== File: assistants/navigator-assistant/README.md ===
# Navigator Assistant

This assistant is designed to help with navigating the Semantic Workbench application and assistants.

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


=== File: assistants/navigator-assistant/pyproject.toml ===
[project]
name = "navigator-assistant"
version = "0.1.0"
description = "A python Semantic Workbench OpenAI assistant for navigating the workbench and assistants."
authors = [{ name = "Semantic Workbench Team" }]
readme = "README.md"
requires-python = ">=3.11,<3.13"
dependencies = [
    "assistant-drive>=0.1.0",
    "assistant-extensions[attachments, mcp]>=0.1.0",
    "mcp-extensions[openai]>=0.1.0",
    "content-safety>=0.1.0",
    "deepmerge>=2.0",
    "openai>=1.61.0",
    "openai-client>=0.1.0",
    "tiktoken>=0.8.0",
]

[tool.hatch.build.targets.wheel]
packages = ["assistant"]

[tool.uv]
package = true

[tool.uv.sources]
anthropic-client = { path = "../../libraries/python/anthropic-client", editable = true }
assistant-drive = { path = "../../libraries/python/assistant-drive", editable = true }
assistant-extensions = { path = "../../libraries/python/assistant-extensions", editable = true }
mcp-extensions = { path = "../../libraries/python/mcp-extensions", editable = true }
content-safety = { path = "../../libraries/python/content-safety/", editable = true }
openai-client = { path = "../../libraries/python/openai-client", editable = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[dependency-groups]
dev = ["pyright>=1.1.389"]


=== File: assistants/project-assistant/README.md ===
# Project Assistant

A dual-mode context transfer system that facilitates collaborative projects between Coordinators and Team members in the Semantic Workbench.

## Overview

The Project Assistant is designed to bridge the information gap between project Coordinators and Team members by providing a structured communication system with shared artifacts, real-time updates, and bidirectional information flow. It enables:

- **Project Definition**: Coordinators can create detailed project briefs with goals and success criteria
- **Information Sharing**: Knowledge transfer between separate conversations
- **Information Requests**: Team members can request information or assistance from Coordinators
- **Progress Tracking**: Real-time project dashboard updates and completion criteria
- **Inspector Panel**: Visual dashboard showing project state and progress

## Key Features

### Conversation Types and Dual Mode Operation 

The Project Assistant creates and manages three distinct types of conversations:

1. **Coordinator Conversation**: The personal conversation used by the project coordinator/owner to create and manage the project.

2. **Shareable Team Conversation**: A template conversation that's automatically created along with a share URL. This conversation is never directly used - it serves as the template for creating individual team conversations when users click the share link.

3. **Team Conversation(s)**: Individual conversations for team members, created when they redeem the share URL. Each team member gets their own personal conversation connected to the project.

The assistant operates in two distinct modes with different capabilities:

1. **Coordinator Mode (Planning Stage)**
   - Create project briefs with clear goals and success criteria
   - Maintain an auto-updating project whiteboard with critical information
   - Provide guidance and respond to information requests
   - Control the "Ready for Working" milestone when project definition is complete

2. **Team Mode (Working Stage)**
   - Access project brief and project whiteboard
   - Mark success criteria as completed
   - Log requests for information or assistance from Coordinators
   - Update project dashboard with progress information
   - Report project completion when all criteria are met

### Key Artifacts

The system manages several core artifacts that support project operations:

- **Project Brief**: Details project goals and success criteria
- **Project Whiteboard**: Dynamically updated information repository that captures key project context
- **Information Requests**: Documented information needs from Team members
- **Project Dashboard**: Real-time progress tracking and state information

### State Management

The assistant uses a multi-layered state management approach:

- **Cross-Conversation Linking**: Connects Coordinator and Team conversations
- **File Synchronization**: Automatic file sharing between conversations, including when files are uploaded by Coordinators or when team members return to a conversation
- **Inspector Panel**: Real-time visual status dashboard for project progress
- **Conversation-Specific Storage**: Each conversation maintains role-specific state

## Usage

### Commands

#### Common Commands
- `/status` - View current project status and progress
- `/info [brief|whiteboard|requests|all]` - View project information

#### Coordinator Commands
- `/create-project <name> | <description>` - Create a new project
- `/add-goal <name> | <description> | [criteria1;criteria2;...]` - Add a project goal
- `/add-kb-section <title> | <content>` - Add whiteboard content manually
- `/ready-for-working` - Mark project as ready for team operations
- `/invite` - Generate project invitation for team members
- `/resolve <request-id> | <resolution>` - Resolve an information request

#### Team Commands
- `/join <invitation-code>` - Join an existing project
- `/request-info <title> | <description> | [priority]` - Create information request
- `/update-status <status> | <progress> | <message>` - Update project status
- `/complete-criteria <goal-index> <criteria-index>` - Mark criterion as complete
- `/complete-project` - Report project completion

### Workflow

1. **Coordinator Preparation**:
   - Create project brief with goals and success criteria
   - The project whiteboard automatically updates with key information
   - Generate invitation link for team members
   - Mark project as ready for working

2. **Team Operations**:
   - Join project using invitation link
   - Review project brief and whiteboard content
   - Execute project tasks and track progress
   - Create information requests when information is needed
   - Mark criteria as completed when achieved
   - Report project completion when all goals are met

3. **Collaborative Cycle**:
   - Coordinator responds to information requests
   - Team updates project status with progress
   - Both sides can view project status and progress via inspector panel

## Development

### Project Structure

- `/assistant/`: Core implementation files
  - `chat.py`: Main assistant implementation with event handlers
  - `project_tools.py`: Tool functions for the LLM to use
  - `state_inspector.py`: Inspector panel implementation
  - `project_manager.py`: Project state and artifact management
  - `artifact_messaging.py`: Cross-conversation artifact sharing
  - `command_processor.py`: Command handling logic

- `/docs/`: Documentation files
  - `DESIGN.md`: System design and architecture
  - `DEV_GUIDE.md`: Development guidelines
  - `ASSISTANT_LIBRARY_NOTES.md`: Notes on the assistant library
  - `WORKBENCH_NOTES.md`: Workbench state management details

- `/tests/`: Test files covering key functionality

### Development Commands

```bash
# Install dependencies
make install

# Run tests
make test

# Type checking
make type-check

# Linting
make lint
```

## Architecture

The Project Assistant leverages the Semantic Workbench Assistant library for core functionality and extends it with:

1. **Cross-Conversation Communication**: Using the conversation sharing API
2. **Artifact Management**: Structured data models for project information
3. **State Inspection**: Real-time project status dashboard
4. **Tool-based Interaction**: LLM functions for project tasks
5. **Role-Specific Experiences**: Tailored interfaces for Coordinator and Team roles

The system follows a centralized artifact storage model with event-driven updates to keep all conversations synchronized.


=== File: assistants/project-assistant/pyproject.toml ===
[project]
name = "assistant"
version = "0.1.0"
description = "A file-sharing mediator assistant for collaborative projects."
authors = [{ name = "Semantic Workbench Team" }]
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "assistant-extensions[attachments]>=0.1.0",
    "content-safety>=0.1.0",
    "deepmerge>=2.0",
    "openai>=1.61.0",
    "openai-client>=0.1.0",
    "semantic-workbench-assistant>=0.1.0",
    "tiktoken>=0.8.0",
]

[dependency-groups]
dev = [
    "pytest>=8.3.1",
    "pytest-asyncio>=0.23.8",
    "pytest-repeat>=0.9.3",
    "pyright>=1.1.389",
]

[tool.uv]
package = true

[tool.uv.sources]
assistant-extensions = { path = "../../libraries/python/assistant-extensions", editable = true }
content-safety = { path = "../../libraries/python/content-safety/", editable = true }
openai-client = { path = "../../libraries/python/openai-client", editable = true }
semantic-workbench-assistant = { path = "../../libraries/python/semantic-workbench-assistant", editable = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pyright]
exclude = ["**/.venv", "**/.data", "**/__pycache__"]

[tool.pytest.ini_options]
addopts = "-vv"
log_cli = true
log_cli_level = "WARNING"
log_cli_format = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"


=== File: assistants/prospector-assistant/README.md ===
# Using Semantic Workbench with python assistants

This project provides an assistant to help mine artifacts for ideas, leveraging OpenAI or Azure OpenAI (or any OpenAI compatible service), allowing to use **Semantic Workbench** to test it.

## Responsible AI

The chatbot includes some important best practices for AI development, such as:

- **System prompt safety**, ie a set of LLM guardrails to protect users. As a developer you should understand how these
  guardrails work in your scenarios, and how to change them if needed. The system prompt and the prompt safety
  guardrails are split in two to help with testing. When talking to LLM models, prompt safety is injected before the
  system prompt.
  - See https://learn.microsoft.com/azure/ai-services/openai/concepts/system-message for more details
    about protecting application and users in different scenarios.
- **Content moderation**, via [Azure AI Content Safety](https://azure.microsoft.com/products/ai-services/ai-content-safety)
  or [OpenAI Content Moderation](https://platform.openai.com/docs/guides/moderation).

See the [Responsible AI FAQ](../../RESPONSIBLE_AI_FAQ.md) for more information.

# Suggested Development Environment

- Use GitHub Codespaces for a quick, turn-key dev environment: [/.devcontainer/README.md](../../.devcontainer/README.md)
- VS Code is recommended for development

## Pre-requisites

- Set up your dev environment
  - SUGGESTED: Use GitHub Codespaces for a quick, easy, and consistent dev
    environment: [/.devcontainer/README.md](../../.devcontainer/README.md)
  - ALTERNATIVE: Local setup following the [main README](../../README.md#local-development-environment)
- Set up and verify that the workbench app and service are running using the [semantic-workbench.code-workspace](../../semantic-workbench.code-workspace)
- If using Azure OpenAI, set up an Azure account and create a Content Safety resource
  - See [Azure AI Content Safety](https://azure.microsoft.com/products/ai-services/ai-content-safety) for more information
  - Copy the `.env.example` to `.env` and update the `ASSISTANT__AZURE_CONTENT_SAFETY_ENDPOINT` value with the endpoint of your Azure Content Safety resource
  - From VS Code > `Terminal`, run `az login` to authenticate with Azure prior to starting the assistant

## Steps

- Use VS Code > `Run and Debug` (ctrl/cmd+shift+d) > `semantic-workbench` to start the app and service from this workspace
- Use VS Code > `Run and Debug` (ctrl/cmd+shift+d) > `launch assistant` to start the assistant.
- If running in a devcontainer, follow the instructions in [.devcontainer/POST_SETUP_README.md](../../.devcontainer/POST_SETUP_README.md#start-the-app-and-service) for any additional steps.
- Return to the workbench app to interact with the assistant
- Add a new assistant from the main menu of the app, choose the assistant name as defined by the `service_name` in [chat.py](./assistant/chat.py)
- Click the newly created assistant to configure and interact with it

## Starting the example from CLI

If you're not using VS Code and/or Codespaces, you can also work from the
command line, using `uv`:

```
cd <PATH TO THIS FOLDER>

uv run start-assistant
```

## Create your own assistant

Copy the contents of this folder to your project.

- The paths are already set if you put in the same repo root and relative path of `/<your_projects>/<your_assistant_name>`
- If placed in a different location, update the references in the `pyproject.toml` to point to the appropriate locations for the `semantic-workbench-*` packages

## From Development to Production

It's important to highlight how Semantic Workbench is a development tool, and it's not designed to host agents in
a production environment. The workbench helps with testing and debugging, in a development and isolated environment, usually your localhost.

The core of your assistant/AI application, e.g. how it reacts to users, how it invokes tools, how it stores data, can be
developed with any framework, such as Semantic Kernel, Langchain, OpenAI assistants, etc. That is typically the code
you will add to `chat.py`.

**Semantic Workbench is not a framework**. Dependencies on `semantic-workbench-assistant` package are used only to test and debug your code in Semantic Workbench. **When an assistant is fully developed and ready for production, configurable settings should be hard coded, dependencies on `semantic-workbench-assistant` and similar should be removed**.


=== File: assistants/prospector-assistant/pyproject.toml ===
[project]
name = "assistant"
version = "0.1.0"
description = "Exploration of a python Semantic Workbench OpenAI assistant to help mine artifacts for ideas."
authors = [{ name = "Semantic Workbench Team" }]
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "assistant-extensions[attachments]>=0.1.0",
    "content-safety>=0.1.0",
    "deepmerge>=2.0",
    "guided-conversation>=0.1.0",
    "html2docx>=1.6.0",
    "markdown>=3.6",
    "openai-client>=0.1.0",
    "openai>=1.61.0",
]

[tool.uv]
package = true

[tool.uv.sources]
assistant-drive = { path = "../../libraries/python/assistant-drive", editable = true }
assistant-extensions = { path = "../../libraries/python/assistant-extensions", editable = true }
content-safety = { path = "../../libraries/python/content-safety/", editable = true }
guided-conversation = { path = "../../libraries/python/guided-conversation", editable = true }
openai-client = { path = "../../libraries/python/openai-client", editable = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[dependency-groups]
dev = [
    "pyright>=1.1.399",
    "pytest>=8.3.4",
    "pytest-asyncio>=0.25.3",
    "pytest-httpx>=0.35.0",
    "pytest-repeat>=0.9.3",
]

[tool.pytest.ini_options]
addopts = "-vv --color=yes"
log_cli = true
log_cli_level = "INFO"
log_cli_format = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"


=== File: assistants/skill-assistant/README.md ===
# Skill Assistant

The Skill Assistant serves as a demonstration of integrating the Skill Library within an Assistant in the Semantic Workbench. Specifically, this assistant showcases the Posix skill and the chat driver. The [Posix skill](../../libraries/python/skills/skills/posix-skill/README.md) demonstrates file system management by allowing the assistant to perform posix-style actions. The [chat driver](../../libraries/python/openai-client/openai_client/chat_driver/README.md) handles conversations and interacts with underlying AI models like OpenAI and Azure OpenAI.

## Overview

[skill_controller.py](assistant/skill_controller.py) file is responsible for managing the assistants. It includes functionality to create and retrieve assistants, configure chat drivers, and map skill events to the Semantic Workbench.

- AssistantRegistry: Manages multiple assistants, each associated with a unique conversation.
- \_event_mapper: Maps skill events to message types understood by the Semantic Workbench.
- create_assistant: Defines how to create and configure a new assistant.

[skill_assistant.py](assistant/skill_assistant.py) file defines the main Skill Assistant class that integrates with the Semantic Workbench. It handles workbench events and coordinates the assistant's responses based on the conversation state.

- SkillAssistant Class: The main class that integrates with the Semantic Workbench.
- on_workbench_event: Handles various workbench events to drive the assistant's behavior.

[config.py](assistant/config.py) file defines the configuration model for the Skill Assistant. It includes settings for both Azure OpenAI and OpenAI services, along with request-specific settings such as max_tokens and response_tokens.

- RequestConfig: Defines parameters for generating responses, including tokens settings.

## Responsible AI

The assistant includes some important best practices for AI development, such as:

- **System prompt safety**, ie a set of LLM guardrails to protect users. As a developer you should understand how these
  guardrails work in your scenarios, and how to change them if needed. The system prompt and the prompt safety
  guardrails are split in two to help with testing. When talking to LLM models, prompt safety is injected before the
  system prompt.
  - See https://learn.microsoft.com/azure/ai-services/openai/concepts/system-message for more details
    about protecting application and users in different scenarios.
- **Content moderation**, via [Azure AI Content Safety](https://azure.microsoft.com/products/ai-services/ai-content-safety)
  or [OpenAI Content Moderation](https://platform.openai.com/docs/guides/moderation).

See the [Responsible AI FAQ](../../RESPONSIBLE_AI_FAQ.md) for more information.

# Suggested Development Environment

- Use GitHub Codespaces for a quick, turn-key dev environment: [/.devcontainer/README.md](../../.devcontainer/README.md)
- VS Code is recommended for development

## Pre-requisites

- Set up your dev environment
  - SUGGESTED: Use GitHub Codespaces for a quick, easy, and consistent dev
    environment: [/.devcontainer/README.md](../../.devcontainer/README.md)
  - ALTERNATIVE: Local setup following the [main README](../../README.md#local-development-environment)
- Set up and verify that the workbench app and service are running using the [semantic-workbench.code-workspace](../../semantic-workbench.code-workspace)
- If using Azure OpenAI, set up an Azure account and create a Content Safety resource
  - See [Azure AI Content Safety](https://azure.microsoft.com/products/ai-services/ai-content-safety) for more information
  - Copy the `.env.example` to `.env` and update the `ASSISTANT__AZURE_CONTENT_SAFETY_ENDPOINT` value with the endpoint of your Azure Content Safety resource
  - From VS Code > `Terminal`, run `az login` to authenticate with Azure prior to starting the assistant

## Steps

- Use VS Code > `Run and Debug` (ctrl/cmd+shift+d) > `semantic-workbench` to start the app and service from this workspace
- Use VS Code > `Run and Debug` (ctrl/cmd+shift+d) > `launch assistant` to start the assistant.
- If running in a devcontainer, follow the instructions in [.devcontainer/POST_SETUP_README.md](../../.devcontainer/POST_SETUP_README.md#start-the-app-and-service) for any additional steps.
- Return to the workbench app to interact with the assistant
- Add a new assistant from the main menu of the app, choose the assistant name as defined by the `service_name` in [chat.py](./assistant/skill_assistant.py)
- Click the newly created assistant to configure and interact with it

## Starting the example from CLI

If you're not using VS Code and/or Codespaces, you can also work from the
command line, using `uv`:

```
cd <PATH TO THIS FOLDER>

uv run start-assistant
```

## Create your own assistant

Copy the contents of this folder to your project.

- The paths are already set if you put in the same repo root and relative path of `/<your_projects>/<your_assistant_name>`
- If placed in a different location, update the references in the `pyproject.toml` to point to the appropriate locations for the `semantic-workbench-*` packages

## From Development to Production

It's important to highlight how Semantic Workbench is a development tool, and it's not designed to host agents in
a production environment. The workbench helps with testing and debugging, in a development and isolated environment, usually your localhost.

The core of your assistant/AI application, e.g. how it reacts to users, how it invokes tools, how it stores data, can be
developed with any framework, such as Semantic Kernel, Langchain, OpenAI assistants, etc. That is typically the code
you will add to `chat.py`.

**Semantic Workbench is not a framework**. Dependencies on `semantic-workbench-assistant` package are used only to test and debug your code in Semantic Workbench. **When an assistant is fully developed and ready for production, configurable settings should be hard coded, dependencies on `semantic-workbench-assistant` and similar should be removed**.


=== File: assistants/skill-assistant/pyproject.toml ===
[project]
name = "assistant"
version = "0.1.0"
description = "MADE:Exploration skill assistant."
authors = [{ name = "MADE:Exploration" }]
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "azure-ai-contentsafety>=1.0.0",
    "azure-core[aio]>=1.30.0",
    "azure-identity>=1.16.0",
    "content-safety>=0.1.0",
    "openai-client>=0.1.0",
    "openai>=1.61.0",
    "semantic-workbench-assistant>=0.1.0",
    "bs4>=0.0.2",
    "skill-library>=0.1.0",
]

[dependency-groups]
dev = [
    "pytest>=8.3.1",
    "pytest-asyncio>=0.23.8",
    "pytest-repeat>=0.9.3",
    "ipykernel>=6.29.4",
    "pyright>=1.1.389",
]

[tool.uv]
package = true

[tool.uv.sources]
skill-library = { path = "../../libraries/python/skills/skill-library", editable = true }
content-safety = { path = "../../libraries/python/content-safety", editable = true }
openai-client = { path = "../../libraries/python/openai-client", editable = true }
semantic-workbench-assistant = { path = "../../libraries/python/semantic-workbench-assistant", editable = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pyright]
exclude = ["**/.venv", "**/.data", "**/__pycache__"]

[tool.pytest.ini_options]
addopts = "-vv"
log_cli = true
log_cli_level = "WARNING"
log_cli_format = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"


