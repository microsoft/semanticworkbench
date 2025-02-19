# MCP Extensions Library

The `mcp-extensions` library is a supplemental toolkit designed to enhance the functionality and usability of the Model Context Protocol (MCP) framework. MCP provides a standardized interface for bridging AI models with external resources, tools, and prompts. This library builds on that foundation by offering utility methods, helper functions, and extended models to improve workflow efficiency and enable advanced integration features.

## What is MCP?

MCP (Model Context Protocol) allows applications to provide structured data sources, executable tools, and reusable prompts to Large Language Models (LLMs) in a standardized way. Using MCP, you can:

- Build MCP clients to communicate with MCP servers.
- Create MCP servers that expose resources, tools, and prompts for model interaction.
- Leverage seamless integrations between your services and LLM applications.

The `mcp-extensions` library supplements this ecosystem to bridge specific gaps in workflows or extend capabilities.

## Features

### 1. Tool Execution Enhancements

- **Notification-based Lifecycles:** Implement `execute_tool_with_notifications` to handle tool calls with real-time notifications to the server. This is particularly valuable for:
  - Progress tracking.
  - Handling asynchronous tool execution.

```python
await execute_tool_with_notifications(
    session=session,
    tool_call_function=my_tool_call,
    notification_handler=handle_server_notifications
)
```

### 2. Conversion Utilities

- **Convert MCP Tools:** Leverages `convert_tools_to_openai_tools` to transform MCP tools into OpenAI-compatible function definitions. Useful for interoperating with ecosystems that leverage OpenAI's function call syntax.

```python
converted_tools = convert_tools_to_openai_tools(mcp_tools, extra_properties={'user_context': 'optional'})
```

### 3. Progress Notifications

- **Report Progress to MCP Clients:**
  Provide fine-grained updates about ongoing tasks using `send_tool_call_progress`. Ideal for applications where the client requires detailed visibility into long-running tasks.

```python
await send_tool_call_progress(context, "50% task completed", data={"step": 3})
```

### 4. Extended Data Models

- **Custom Server Notification Handlers:** Includes extended models like `ToolCallFunction`, `ServerNotificationHandler`, and `ToolCallProgressMessage` for greater flexibility when handling server events and workflow lifecycles.

```python
from mcp_extensions._model import ServerNotificationHandler, ToolCallProgressMessage
```

## Use Cases

### A. Enhanced Tool Lifecycle Management

The library helps in managing tool lifecycles—for asynchronous executions, task progress reporting, and server-side notification handling.

### B. Cross-Ecosystem Interoperability

By transforming MCP tool definitions to OpenAI's tool schema, the library facilitates hybrid use cases where functionality needs to work seamlessly across frameworks.

### C. Real-Time Execution Feedback

Applications requiring frequent updates about task statuses benefit from the notification-based features built into the library.

## Installation

To install the `mcp-extensions` library, run:

```bash
pip install mcp-extensions
```

Ensure that you are using Python 3.11 or later to leverage the library's features.

## Supported Dependencies

The library depends on:

- `deepmerge`: For combining tool properties with additional metadata.
- `mcp`: Required for core protocol interactions.

Optional:

- `openai`: If integrating with OpenAI's APIs.

## Getting Started

Here is a minimal example to use the library’s tool execution utilities:

```python
from mcp_extensions import execute_tool_with_notifications

async def my_tool_call():
    # Perform tool-specific task
    return {"result": "completed"}

async def handle_server_notifications(notification):
    print(f"Received server notification: {notification}")

await execute_tool_with_notifications(
    session=session,
    tool_call_function=my_tool_call,
    notification_handler=handle_server_notifications
)
```

---

For more information on the Model Context Protocol, visit the [official documentation](https://modelcontextprotocol.io).
