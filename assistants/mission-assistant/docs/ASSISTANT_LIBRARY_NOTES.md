# Semantic Workbench Assistant Library

This document provides an overview of the Semantic Workbench Assistant library found in `/workspaces/semanticworkbench/libraries/python/semantic-workbench-assistant/semantic_workbench_assistant`.

## Overview

The semantic-workbench-assistant library provides a framework for building assistants that integrate with the Semantic Workbench platform. It handles communication protocols, state management, event handling, and provides an abstraction layer that simplifies assistant development.

## Key Components

### Core Classes

- **AssistantApp**: The main entry point for creating assistants with event subscriptions.
  - Configures service metadata, capabilities, and providers
  - Initializes event handling system
  - Creates the FastAPI application

- **ConversationContext**: Interface for interacting with conversations
  - Manages messages, files, and conversation state
  - Provides methods for conversation operations
  - Integrates with the Workbench client for API operations

- **AssistantContext**: Holds information about the assistant identity

### State Management

- **File-based persistence**:
  - `storage.py` provides `read_model()` and `write_model()` for serializing Pydantic models to files
  - Models are stored as JSON in a configurable storage directory
  - `storage_directory_for_context()` creates unique paths for each assistant/conversation

- **Context objects**:
  - `AssistantContext` and `ConversationContext` serve as state containers
  - Conversation-specific operations are accessed through the context

### Communication

- **Event-driven architecture**:
  - Assistants subscribe to conversation events (messages, participants, files)
  - Asynchronous event processing queues decouple event reception from handling
  - Event system notifies the assistant of changes to track state

- **API Integration**:
  - Uses a client to communicate with the Workbench service
  - Provides methods for sending messages, managing files, and updating state

## Usage for Mission Assistant

For the Mission Assistant, the library provides:

1. **File storage mechanisms** for persisting mission state between sessions
2. **Context objects** for accessing conversation data and performing operations
3. **Event handling** for reacting to changes in conversations
4. **Cross-conversation capabilities** through API clients
5. **Abstraction layer** for Workbench service integration

## Implementation Details

### Storage Pattern

```python
# Example of reading/writing models
from semantic_workbench_assistant.storage import read_model, write_model

# Write a model to storage
def save_state(context, data):
    path = storage_directory_for_context(context) / "mission_data.json"
    write_model(path, data)

# Read a model from storage
def load_state(context, model_class):
    path = storage_directory_for_context(context) / "mission_data.json"
    return read_model(path, model_class)
```

### Context Usage

```python
# Example of context methods
async def process_message(context: ConversationContext, message):
    # Send a response
    await context.send_messages(NewConversationMessage(
        content="Processing your request", 
        message_type=MessageType.chat
    ))
    
    # Access files
    files = await context.get_files()
    
    # Update conversation state
    await context.send_conversation_state_event(
        AssistantStateEvent(state_id="mission_status", event="updated", state=None)
    )
```