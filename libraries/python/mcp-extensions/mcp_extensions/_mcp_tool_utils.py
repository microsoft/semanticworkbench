# utils/tool_utils.py
import asyncio
import logging
from typing import Any, List

import deepmerge
from mcp import ClientSession, ServerNotification, Tool
from mcp.server.fastmcp import Context
from mcp.shared.session import BaseSession
from mcp.types import CallToolResult
from openai.types.chat import (
    ChatCompletionToolParam,
)
from openai.types.shared_params import FunctionDefinition

from ._model import ServerNotificationHandler, ToolCallFunction

logger = logging.getLogger(__name__)


async def send_tool_call_progress(
    fastmcp_server_context: Context, message: str, data: dict[str, Any] | None = None
) -> None:
    """
    Send a progress update message for a tool call to the FastMCP server.
    """

    session: BaseSession = fastmcp_server_context.session
    await session.send_log_message(
        level="info",
        data=message,
    )

    # FIXME: Would prefer to use this to send data via a custom notification, but it's not working
    # jsonrpc_notification = JSONRPCNotification(
    #     method="tool_call_progress",
    #     jsonrpc="2.0",
    #     params=ToolCallProgressMessage(
    #         message=message,
    #         data=data,
    #     ).model_dump(mode="json"),
    # )
    # await session._write_stream.send(JSONRPCMessage(jsonrpc_notification))


async def execute_tool_with_notifications(
    session: ClientSession,
    tool_call_function: ToolCallFunction,
    notification_handler: ServerNotificationHandler,
) -> CallToolResult:
    """
    Execute a tool call while handling notifications that may arrive during execution.

    Args:
        session: The MCP client session
        tool_call: Async function that performs the actual tool call
        notification_handler: Async function to handle notifications during execution

    Returns:
        The result of the tool call
    """

    # Create a task for listening to incoming messages
    async def message_listener() -> None:
        async for message in session.incoming_messages:
            if isinstance(message, Exception):
                raise message
            if isinstance(message, ServerNotification):
                await notification_handler(message)
            else:
                logger.warning(f"Received unknown message: {message}")

    # Create a task group to run both the tool call and message listener
    async with asyncio.TaskGroup() as task_group:
        # Start the message listener
        listener_task = task_group.create_task(message_listener())

        try:
            # Execute the tool call
            result = await tool_call_function()
            return result
        finally:
            # Cancel the listener task when we're done
            listener_task.cancel()


def convert_tools_to_openai_tools(
    mcp_tools: List[Tool] | None, extra_properties: dict[str, Any] | None = None
) -> List[ChatCompletionToolParam] | None:
    """
    Convert MCP tools to OpenAI tools. Use the extra properties to add additional parameters,
    such as a custom property to allow the model to explain the reason for the tool call.
    """

    if not mcp_tools:
        return None

    openai_tools: List[ChatCompletionToolParam] = []
    for mcp_tool in mcp_tools:
        parameters = mcp_tool.inputSchema.copy()

        if isinstance(extra_properties, dict):
            # Add the extra properties to the input schema
            parameters = deepmerge.always_merger.merge(
                parameters,
                {
                    "properties": {
                        **extra_properties,
                    },
                    "required": [
                        *extra_properties.keys(),
                    ],
                },
            )

        function = FunctionDefinition(
            name=mcp_tool.name,
            description=mcp_tool.description if mcp_tool.description else "[no description provided]",
            parameters=parameters,
        )

        openai_tools.append(
            ChatCompletionToolParam(
                function=function,
                type="function",
            )
        )

    return openai_tools
