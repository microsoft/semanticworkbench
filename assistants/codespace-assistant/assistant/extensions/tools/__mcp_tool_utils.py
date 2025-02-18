# utils/tool_utils.py
import asyncio
import logging
from collections.abc import Awaitable
from textwrap import dedent
from typing import AsyncGenerator, Callable, List, TypeVar

import deepmerge
from anyio.streams.memory import MemoryObjectReceiveStream
from mcp import ClientSession, ServerNotification, Tool
from mcp.types import CallToolResult, EmbeddedResource, ImageContent, TextContent

from .__model import MCPSession, OnLoggingMessageHandler, ToolCall, ToolCallResult, ToolMessageType, ToolsConfigModel

logger = logging.getLogger(__name__)


def retrieve_tools_from_sessions(mcp_sessions: List[MCPSession], tools_config: ToolsConfigModel) -> List[Tool]:
    """
    Retrieve tools from all MCP sessions, excluding any tools that are disabled in the tools config.
    """
    return [
        tool
        for mcp_session in mcp_sessions
        for tool in mcp_session.tools
        if tool.name not in tools_config.tools_disabled
    ]


def get_mcp_session_and_tool_by_tool_name(
    mcp_sessions: List[MCPSession],
    tool_name: str,
) -> tuple[MCPSession | None, Tool | None]:
    """
    Retrieve the MCP session and tool by tool name.
    """
    return next(
        ((mcp_session, tool) for mcp_session in mcp_sessions for tool in mcp_session.tools if tool.name == tool_name),
        (None, None),
    )


async def handle_tool_call(
    mcp_sessions: List[MCPSession],
    tool_call: ToolCall,
    method_metadata_key: str,
    on_logging_message: OnLoggingMessageHandler,
) -> ToolCallResult:
    """
    Handle the tool call by invoking the appropriate tool and returning a ToolCallResult.
    """

    # Find the tool and session from the full collection of sessions
    mcp_session, tool = get_mcp_session_and_tool_by_tool_name(mcp_sessions, tool_call.name)

    if not mcp_session or not tool:
        return ToolCallResult(
            id=tool_call.id,
            content=f"Tool '{tool_call.name}' not found in any of the sessions.",
            message_type=ToolMessageType.notice,
            metadata={},
        )

    return await execute_tool(mcp_session, tool_call, method_metadata_key, on_logging_message)


async def handle_long_running_tool_call(
    mcp_sessions: List[MCPSession],
    tool_call: ToolCall,
    method_metadata_key: str,
    on_logging_message: OnLoggingMessageHandler,
) -> AsyncGenerator[ToolCallResult, None]:
    """
    Handle the streaming tool call by invoking the appropriate tool and returning a ToolCallResult.
    """

    # Find the tool and session from the full collection of sessions
    mcp_session, tool = get_mcp_session_and_tool_by_tool_name(mcp_sessions, tool_call.name)

    if not mcp_session or not tool:
        yield ToolCallResult(
            id=tool_call.id,
            content=f"Tool '{tool_call.name}' not found in any of the sessions.",
            message_type=ToolMessageType.notice,
            metadata={},
        )
        return

    # For now, let's just hack to return an immediate response to indicate that the tool call was received
    # and is being processed and that the results will be sent in a separate message.
    yield ToolCallResult(
        id=tool_call.id,
        content=dedent(f"""
            Processing tool call '{tool_call.name}'.
            Estimated time to completion: {mcp_session.config.task_completion_estimate}
        """).strip(),
        message_type=ToolMessageType.tool_result,
        metadata={},
    )

    # Perform the tool call
    tool_call_result = await execute_tool(mcp_session, tool_call, method_metadata_key, on_logging_message)
    yield tool_call_result


async def listen_to_incoming_messages(
    incoming_messages: MemoryObjectReceiveStream, on_logging_message: OnLoggingMessageHandler
) -> None:
    try:
        async with incoming_messages:
            async for message in incoming_messages:
                if isinstance(message, ServerNotification):
                    if message.root.method == "notifications/message":
                        logger.info(f"Received message: {message.root.params.data}")
                        on_logging_message(message.root.params.data)
                    else:
                        logger.warning(f"Received unknown notification: {message}")
                else:
                    logger.warning(f"Received unknown message: {message}")
    except asyncio.CancelledError:
        # Properly exit when the task is cancelled
        return


T = TypeVar("T")  # Type variable for the tool call result


async def execute_tool_with_notifications(
    session: ClientSession,
    tool_call: Callable[[], Awaitable[T]],
    notification_handler: Callable[[ServerNotification], Awaitable[None]],
) -> T:
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
            result = await tool_call()
            return result
        finally:
            # Cancel the listener task when we're done
            listener_task.cancel()


async def execute_tool(
    mcp_session: MCPSession,
    tool_call: ToolCall,
    method_metadata_key: str,
    on_logging_message: OnLoggingMessageHandler,
) -> ToolCallResult:
    # Initialize metadata
    metadata = {}

    # Initialize tool_result
    tool_result = None
    tool_output: list[TextContent | ImageContent | EmbeddedResource] = []
    content_items: List[str] = []

    async def tool_call_function() -> CallToolResult:
        return await mcp_session.client_session.call_tool(tool_call.name, tool_call.arguments)

    async def notification_handler(message: ServerNotification) -> None:
        if message.root.method == "notifications/message":
            await on_logging_message(message.root.params.data)
        else:
            logger.warning(f"Received unknown notification: {message}")

    logger.debug(f"Invoking '{mcp_session.config.key}.{tool_call.name}' with arguments: {tool_call.arguments}")
    tool_result = await execute_tool_with_notifications(
        mcp_session.client_session, tool_call_function, notification_handler
    )
    tool_output = tool_result.content

    # Update metadata with tool result
    deepmerge.always_merger.merge(
        metadata,
        {
            "debug": {
                method_metadata_key: {
                    "tool_result": tool_output,
                },
            },
        },
    )

    for tool_output_item in tool_output:
        if isinstance(tool_output_item, TextContent):
            content_items.append(tool_output_item.text)
        if isinstance(tool_output_item, ImageContent):
            content_items.append(tool_output_item.model_dump_json())
        if isinstance(tool_output_item, EmbeddedResource):
            content_items.append(tool_output_item.model_dump_json())

    # Return the tool call result
    return ToolCallResult(
        id=tool_call.id,
        content="\n\n".join(content_items),
        message_type=ToolMessageType.tool_result,
        metadata=metadata,
    )


# async def execute_tool_call(
#     mcp_session: MCPSession,
#     tool_call: ToolCall,
#     method_metadata_key: str,
#     on_logging_message: OnLoggingMessageHandler,
# ) -> ToolCallResult:
#     # Initialize metadata
#     metadata = {}

#     # Initialize tool_result
#     tool_result = None
#     tool_output: list[TextContent | ImageContent | EmbeddedResource] = []
#     content_items: List[str] = []

#     async with create_task_group() as task_group:
#         try:
#             # Start processing incoming messages concurrently.
#             task_group.start_soon(
#                 listen_to_incoming_messages,
#                 mcp_session.client_session.incoming_messages,
#                 on_logging_message,
#             )

#             # Start the tool call as a task and wait for it to complete.
#             logger.debug(f"Invoking '{mcp_session.config.key}.{tool_call.name}' with arguments: {tool_call.arguments}")
#             tool_result = await task_group.start(
#                 mcp_session.client_session.call_tool, tool_call.name, tool_call.arguments
#             )
#             tool_output = tool_result.content

#         except Exception as e:
#             logger.exception(f"Error executing tool '{tool_call.name}': {e}")
#             content_items.append(f"An error occurred while executing the tool '{tool_call.to_json()}': {e}")

#         finally:
#             # Clean up: cancel all running tasks and close the incoming messages stream.
#             task_group.cancel_scope.cancel()
#             await mcp_session.client_session.incoming_messages.aclose()

#         # Update metadata with tool result
#         deepmerge.always_merger.merge(
#             metadata,
#             {
#                 "debug": {
#                     method_metadata_key: {
#                         "tool_result": tool_output,
#                     },
#                 },
#             },
#         )

#         for tool_output_item in tool_output:
#             if isinstance(tool_output_item, TextContent):
#                 content_items.append(tool_output_item.text)
#             if isinstance(tool_output_item, ImageContent):
#                 content_items.append(tool_output_item.model_dump_json())
#             if isinstance(tool_output_item, EmbeddedResource):
#                 content_items.append(tool_output_item.model_dump_json())

#         # Return the tool call result
#         return ToolCallResult(
#             id=tool_call.id,
#             content="\n\n".join(content_items),
#             message_type=ToolMessageType.tool_result,
#             metadata=metadata,
#         )
