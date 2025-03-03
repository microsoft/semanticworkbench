# Assistant Extensions

Extensions that enhance Semantic Workbench assistants with additional capabilities beyond the core functionality.

## Overview

The `assistant-extensions` library provides several modules that can be integrated with your Semantic Workbench assistants:

- **Artifacts**: Create and manage file artifacts during conversations (markdown, code, mermaid diagrams, etc.)
- **Attachments**: Process and extract content from file attachments added to conversations
- **AI Clients**: Configure and manage different AI service providers (OpenAI, Azure OpenAI, Anthropic)
- **MCP (Model Context Protocol)**: Connect to and utilize MCP tool servers for extended functionality
- **Workflows**: Define and execute multi-step automated workflows

These extensions are designed to work with the `semantic-workbench-assistant` framework and can be added to your assistant implementation to enhance its capabilities.

## Module Details

### Artifacts

The Artifacts extension enables assistants to create and manage rich content artifacts within conversations.

```python
from assistant_extensions.artifacts import ArtifactsExtension, ArtifactsConfigModel
from semantic_workbench_assistant import AssistantApp

async def get_artifacts_config(context):
    return ArtifactsConfigModel(enabled=True)

# Create and add the extension to your assistant
assistant = AssistantApp(name="My Assistant")
artifacts_extension = ArtifactsExtension(
    assistant=assistant,
    config_provider=get_artifacts_config
)

# The extension is now ready to create and manage artifacts
```

Supports content types including Markdown, code (with syntax highlighting), Mermaid diagrams, ABC notation for music, and more.

### Attachments

Process files uploaded during conversations, extracting and providing content to the AI model.

```python
from assistant_extensions.attachments import AttachmentsExtension, AttachmentsConfigModel
from semantic_workbench_assistant import AssistantApp

assistant = AssistantApp(name="My Assistant")
attachments_extension = AttachmentsExtension(assistant=assistant)

@assistant.events.conversation.message.chat.on_created
async def handle_message(context, event, message):
    config = AttachmentsConfigModel(
        context_description="Files attached to this conversation"
    )
    # Get attachment content to include in AI prompt
    messages = await attachments_extension.get_completion_messages_for_attachments(context, config)
    # Use messages in your AI completion request
```

Supports text files, PDFs, Word documents, and images with OCR capabilities.

### AI Clients

Configuration models for different AI service providers to simplify client setup.

```python
from assistant_extensions.ai_clients.config import OpenAIClientConfigModel, AIServiceType
from openai_client import OpenAIServiceConfig, OpenAIRequestConfig

# Configure an OpenAI client
config = OpenAIClientConfigModel(
    ai_service_type=AIServiceType.OpenAI,
    service_config=OpenAIServiceConfig(
        api_key=os.environ.get("OPENAI_API_KEY")
    ),
    request_config=OpenAIRequestConfig(
        model="gpt-4o",
        temperature=0.7
    )
)

# Use this config with openai_client or anthropic_client libraries
```

### MCP (Model Context Protocol)

Connect to and utilize MCP tool servers to extend your assistant with external capabilities.

```python
from assistant_extensions.mcp import establish_mcp_sessions, retrieve_mcp_tools_from_sessions
from contextlib import AsyncExitStack

async def setup_mcp_tools(config):
    async with AsyncExitStack() as stack:
        # Connect to MCP servers and get available tools
        sessions = await establish_mcp_sessions(config, stack)
        tools = retrieve_mcp_tools_from_sessions(sessions, config)
        
        # Use tools with your AI model
        return sessions, tools
```

### Workflows

Define and execute multi-step workflows within conversations, such as automated sequences.

```python
from assistant_extensions.workflows import WorkflowsExtension, WorkflowsConfigModel
from semantic_workbench_assistant import AssistantApp

async def get_workflows_config(context):
    return WorkflowsConfigModel(
        enabled=True,
        workflow_definitions=[
            {
                "workflow_type": "user_proxy",
                "command": "analyze_document",
                "name": "Document Analysis",
                "description": "Analyze a document for quality and completeness",
                "user_messages": [
                    {"message": "Please analyze this document for accuracy"},
                    {"message": "What improvements would you suggest?"}
                ]
            }
        ]
    )

assistant = AssistantApp(name="My Assistant")
workflows_extension = WorkflowsExtension(
    assistant=assistant,
    config_provider=get_workflows_config
)
```

## Integration

These extensions are designed to enhance Semantic Workbench assistants. To use them:

1. Configure your assistant using the `semantic-workbench-assistant` framework
2. Add the desired extensions to your assistant
3. Implement event handlers for extension functionality 
4. Configure extension behavior through their respective config models

For detailed examples, see the [Assistant Development Guide](../../docs/ASSISTANT_DEVELOPMENT_GUIDE.md) and explore the existing assistant implementations in the repository.

## Optional Dependencies

Some extensions require additional packages:

```
# For attachments support (PDF, Word docs)
pip install "assistant-extensions[attachments]"

# For MCP tool support
pip install "assistant-extensions[mcp]"
```

This library is part of the Semantic Workbench project, which provides a complete framework for building and deploying intelligent assistants.