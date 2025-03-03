# Semantic Workbench Assistant Development Guide

## Overview

For assistants to be instantiated in Semantic Workbench, you need to implement an assistant service that the workbench can talk with via HTTP. Assistants in Semantic Workbench follow a modern architecture with support for extensions, event-driven interactions, and flexible configuration.

We provide several Python base classes to make this easier: [semantic-workbench-assistant](../libraries/python/semantic-workbench-assistant/README.md)

Example assistant services:

- [Canonical assistant example](../libraries/python/semantic-workbench-assistant/semantic_workbench_assistant/canonical.py) - A simple starting point
- Python assistants: [python-01-echo-bot](../examples/python/python-01-echo-bot/README.md) and [python-02-simple-chatbot](../examples/python/python-02-simple-chatbot/README.md)
- .NET agents: [dotnet-01-echo-bot](../examples/dotnet/dotnet-01-echo-bot/README.md), [dotnet-02-message-types-demo](../examples/dotnet/dotnet-02-message-types-demo/README.md) and [dotnet-03-simple-chatbot](../examples/dotnet/dotnet-03-simple-chatbot/README.md)
- Advanced assistants: [explorer-assistant](../assistants/explorer-assistant) and [codespace-assistant](../assistants/codespace-assistant)

## Top level concepts

### AssistantApp

RECOMMENDED FOR PYTHON: Use the `AssistantApp` class from the `semantic-workbench-assistant` package to create your assistant service. This class provides a robust framework for building assistants with event handling, configuration management, and extension support.

```python
from semantic_workbench_assistant.assistant_app import AssistantApp

# Create the AssistantApp instance
assistant = AssistantApp(
    assistant_service_id="your-assistant-id",
    assistant_service_name="Your Assistant Name",
    assistant_service_description="Description of your assistant",
    config_provider=your_config_provider,
    content_interceptor=content_safety,  # Optional content safety
)

# Create a FastAPI app from the assistant
app = assistant.fastapi_app()
```

This approach provides a complete assistant service with event handlers, configuration management, and extension support.

### Configuration with Pydantic Models

Assistant configurations are defined using Pydantic models with UI annotations for rendering in the workbench interface:

```python
from pydantic import BaseModel, Field
from typing import Annotated

class AssistantConfigModel(BaseModel):
    welcome_message: Annotated[
        str,
        Field(
            title="Welcome Message",
            description="Message sent when the assistant joins a conversation"
        )
    ] = "Hello! I'm your assistant. How can I help you today?"
    
    only_respond_to_mentions: Annotated[
        bool,
        Field(
            title="Only respond to @mentions",
            description="Only respond when explicitly mentioned"
        )
    ] = False
```

### Event Handling System

Assistants use a decorator-based event system to respond to conversation events:

```python
@assistant.events.conversation.message.chat.on_created
async def on_message_created(
    context: ConversationContext, event: ConversationEvent, message: ConversationMessage
) -> None:
    # Handle new chat messages here
    await context.send_messages(
        NewConversationMessage(
            content="I received your message!",
            message_type=MessageType.chat
        )
    )

@assistant.events.conversation.on_created
async def on_conversation_created(context: ConversationContext) -> None:
    # Send welcome message when assistant joins a conversation
    await context.send_messages(
        NewConversationMessage(
            content="Hello! I'm your assistant.",
            message_type=MessageType.chat
        )
    )
```

## Extensions

Semantic Workbench assistants can leverage various extensions to enhance functionality:

### Artifacts Extension

Create and manage rich content artifacts within conversations:

```python
from assistant_extensions.artifacts import ArtifactsExtension, ArtifactsConfigModel

artifacts_extension = ArtifactsExtension(
    assistant=assistant,
    config_provider=artifacts_config_provider
)
```

### Attachments Extension

Process files uploaded during conversations:

```python
from assistant_extensions.attachments import AttachmentsExtension

attachments_extension = AttachmentsExtension(assistant=assistant)

# Use in message handler
messages = await attachments_extension.get_completion_messages_for_attachments(context, config)
```

### Workflows Extension

Define and execute multi-step automated workflows:

```python
from assistant_extensions.workflows import WorkflowsExtension, WorkflowsConfigModel

workflows_extension = WorkflowsExtension(
    assistant=assistant,
    content_safety_metadata_key="content_safety",
    config_provider=workflows_config_provider
)
```

### MCP Tools Extension

Connect to Model Context Protocol (MCP) servers for extended functionality:

```python
from assistant_extensions.mcp import establish_mcp_sessions, retrieve_mcp_tools_from_sessions
from contextlib import AsyncExitStack

async with AsyncExitStack() as stack:
    mcp_sessions = await establish_mcp_sessions(config, stack)
    tools = retrieve_mcp_tools_from_sessions(sessions, config)
```

## Content Safety

Assistants can implement content safety evaluators to ensure safe interactions:

```python
from content_safety.evaluators import CombinedContentSafetyEvaluator
from semantic_workbench_assistant.assistant_app import ContentSafety

async def content_evaluator_factory(context: ConversationContext) -> ContentSafetyEvaluator:
    config = await assistant_config.get(context.assistant)
    return CombinedContentSafetyEvaluator(config.content_safety_config)

content_safety = ContentSafety(content_evaluator_factory)
```

## LLM Integration

Assistants can support multiple LLM providers, including OpenAI and Anthropic:

```python
# OpenAI example
from openai_client import create_client, OpenAIServiceConfig, OpenAIRequestConfig

client = create_client(
    service_config=OpenAIServiceConfig(api_key=api_key),
    request_config=OpenAIRequestConfig(model="gpt-4o")
)

# Anthropic example
from anthropic_client import create_client, AnthropicServiceConfig, AnthropicRequestConfig

client = create_client(
    service_config=AnthropicServiceConfig(api_key=api_key),
    request_config=AnthropicRequestConfig(model="claude-3-opus-20240229")
)
```

## Common Patterns

### Message Response Logic

Implement filtering for messages the assistant should respond to:

```python
async def should_respond_to_message(context: ConversationContext, message: ConversationMessage) -> bool:
    # Ignore messages directed at other participants
    if message.metadata.get("directed_at") and message.metadata["directed_at"] != context.assistant.id:
        return False
        
    # Only respond to mentions if configured
    if config.only_respond_to_mentions and f"@{context.assistant.name}" not in message.content:
        # Notify user if needed
        return False
        
    return True
```

### Status Management

Update the assistant's status during processing:

```python
async with context.set_status("thinking..."):
    # Process the message
    await generate_response(context)
```

### Error Handling

Implement robust error handling with debug metadata:

```python
try:
    await respond_to_conversation(context, config)
except Exception as e:
    logger.exception(f"Exception occurred responding to conversation: {e}")
    deepmerge.always_merger.merge(metadata, {"debug": {"error": str(e)}})
    await context.send_messages(
        NewConversationMessage(
            content="An error occurred. View debug inspector for more information.",
            message_type=MessageType.notice,
            metadata=metadata
        )
    )
```

## Frontend Integration

Assistants can integrate with the Semantic Workbench frontend app to provide a rich user experience. The frontend is built using React/TypeScript with Fluent UI components.

### Message Types

The workbench app supports several message types that assistants can use for different purposes:

- **Chat**: Standard conversation messages (primary communication)
- **Notice**: System-like messages that display as a single line
- **Note**: Messages that provide additional information outside the conversation flow
- **Log**: Messages that don't appear in the UI but are available to assistants
- **Command/Command Response**: Special messages prefixed with `/` to invoke commands

```python
await context.send_messages(
    NewConversationMessage(
        content="This is a system notice",
        message_type=MessageType.notice,
        metadata={"attribution": "System"}
    )
)
```

### Message Metadata

Messages can include metadata to enhance their display and behavior:

- **attribution**: Source information displayed after the sender name
- **debug**: Debugging information displayed in a popup
- **footer_items**: Additional information displayed at the bottom of messages
- **directed_at**: Target participant for commands
- **href**: Links for navigation within the app

```python
metadata = {
    "debug": {"tokens_used": 520, "model": "gpt-4o"},
    "footer_items": ["520 tokens used", "Response time: 1.2s"]
}
```

### Frontend Components

The workbench app provides components that assistants can leverage:

- **Content Renderers**: Support for markdown, code, mermaid diagrams, ABC notation
- **Conversation Canvas**: Interactive workspace for conversations
- **Debug Inspector**: Visualizer for message metadata and debugging
- **File Attachments**: Support for attached files and documents

For full documentation on frontend integration, see [/workbench-app/docs](../workbench-app/docs/).

## Assistant Service Development: Getting Started

### Project Structure

A typical assistant project structure:

```
your-assistant/
├── Makefile
├── README.md
├── assistant/
│   ├── __init__.py
│   ├── chat.py          # Main assistant implementation
│   ├── config.py        # Configuration models
│   ├── response/        # Response generation logic
│   │   ├── __init__.py
│   │   └── response.py
│   └── text_includes/   # Prompt templates and other text resources
│       └── guardrails_prompt.txt
├── pyproject.toml       # Project dependencies
└── uv.lock              # Lock file for dependencies
```

### Development Steps

1. Create a fork of this repository
2. Set up your dev environment:
   - SUGGESTED: Use GitHub Codespaces for a quick, consistent dev environment: [/.devcontainer/README.md](../.devcontainer/README.md)
   - ALTERNATIVE: Local setup following the [main README](../README.md#local-development-environment)
3. Create a directory for your assistant in the appropriate location
4. Start building your assistant:
   - Copy and modify an existing assistant (explorer-assistant or codespace-assistant for advanced features)
   - Configure your environment variables (.env file)
5. Build and launch your assistant, then connect it to the workbench via the UI

## Assistant Service Deployment

DISCLAIMER: The security considerations of hosting a service with a public endpoint are beyond the scope of this document. Please ensure you understand the implications of hosting a service before doing so. It is not recommended to host a publicly available instance of the Semantic Workbench app.

If you want to deploy your assistant service to a public endpoint, you will need to create your own Azure app registration and update the app and service files with the new app registration details. See the [Custom app registration](../docs/CUSTOM_APP_REGISTRATION.md) guide for more information.

### Deployment Steps

- Create a new Azure app registration
- Update your app and service files with the new app registration details
- Deploy your service to an endpoint accessible by your web browser
- Update the workbench app with the new service URL
- Deploy your assistant service to an endpoint that the workbench service can access
  - **Suggested**: limit access to the assistant service to only the workbench service using a private network or other security measures
- Deploy the workbench app to an endpoint that users can access
  - **Suggested**: limit access to the workbench app to only trusted users
