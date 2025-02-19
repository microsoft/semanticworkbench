# utils/tool_utils.py
import logging
from textwrap import dedent
from typing import AsyncGenerator, List

import deepmerge
from mcp import ServerNotification, Tool
from mcp.types import CallToolResult, EmbeddedResource, ImageContent, TextContent
from mcp_extensions import execute_tool_with_notifications

from ._model import (
    ExtendedCallToolRequestParams,
    ExtendedCallToolResult,
    MCPSession,
    MCPToolsConfigModel,
    OnMCPLoggingMessageHandler,
)

logger = logging.getLogger(__name__)


def retrieve_mcp_tools_from_sessions(
    mcp_sessions: List[MCPSession], tools_config: MCPToolsConfigModel
) -> List[Tool]:
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
        (
            (mcp_session, tool)
            for mcp_session in mcp_sessions
            for tool in mcp_session.tools
            if tool.name == tool_name
        ),
        (None, None),
    )


async def handle_mcp_tool_call(
    mcp_sessions: List[MCPSession],
    tool_call: ExtendedCallToolRequestParams,
    method_metadata_key: str,
    on_logging_message: OnMCPLoggingMessageHandler,
) -> ExtendedCallToolResult:
    """
    Handle the tool call by invoking the appropriate tool and returning a ToolCallResult.
    """

    # Find the tool and session from the full collection of sessions
    mcp_session, tool = get_mcp_session_and_tool_by_tool_name(
        mcp_sessions, tool_call.name
    )

    if not mcp_session or not tool:
        return ExtendedCallToolResult(
            id=tool_call.id,
            content=[
                TextContent(
                    type="text",
                    text=f"Tool '{tool_call.name}' not found in any of the sessions.",
                )
            ],
            isError=True,
            metadata={},
        )

    return await execute_tool(
        mcp_session, tool_call, method_metadata_key, on_logging_message
    )


async def handle_long_running_tool_call(
    mcp_sessions: List[MCPSession],
    tool_call: ExtendedCallToolRequestParams,
    method_metadata_key: str,
    on_logging_message: OnMCPLoggingMessageHandler,
) -> AsyncGenerator[ExtendedCallToolResult, None]:
    """
    Handle the streaming tool call by invoking the appropriate tool and returning a ToolCallResult.
    """

    # Find the tool and session from the full collection of sessions
    mcp_session, tool = get_mcp_session_and_tool_by_tool_name(
        mcp_sessions, tool_call.name
    )

    if not mcp_session or not tool:
        yield ExtendedCallToolResult(
            id=tool_call.id,
            content=[
                TextContent(
                    type="text",
                    text=f"Tool '{tool_call.name}' not found in any of the sessions.",
                )
            ],
            isError=True,
            metadata={},
        )
        return

    # For now, let's just hack to return an immediate response to indicate that the tool call was received
    # and is being processed and that the results will be sent in a separate message.
    yield ExtendedCallToolResult(
        id=tool_call.id,
        content=[
            TextContent(
                type="text",
                text=dedent(f"""
                Processing tool call '{tool_call.name}'.
                Estimated time to completion: {mcp_session.config.task_completion_estimate}
            """).strip(),
            ),
        ],
        metadata={},
    )

    # Perform the tool call
    tool_call_result = await execute_tool(
        mcp_session, tool_call, method_metadata_key, on_logging_message
    )
    yield tool_call_result


async def execute_tool(
    mcp_session: MCPSession,
    tool_call: ExtendedCallToolRequestParams,
    method_metadata_key: str,
    on_logging_message: OnMCPLoggingMessageHandler,
) -> ExtendedCallToolResult:
    # Initialize metadata
    metadata = {}

    # Initialize tool_result
    tool_result = None
    tool_output: list[TextContent | ImageContent | EmbeddedResource] = []
    content_items: List[str] = []

    async def tool_call_function() -> CallToolResult:
        return await mcp_session.client_session.call_tool(
            tool_call.name, tool_call.arguments
        )

    async def notification_handler(message: ServerNotification) -> None:
        if message.root.method == "notifications/message":
            await on_logging_message(message.root.params.data)
        else:
            logger.warning(f"Received unknown notification: {message}")

    logger.debug(
        f"Invoking '{mcp_session.config.key}.{tool_call.name}' with arguments: {tool_call.arguments}"
    )
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

    # FIXME: for now, we'll just dump the tool output as text but we should support other content types
    for tool_output_item in tool_output:
        if isinstance(tool_output_item, TextContent):
            if tool_output_item.text.strip() != "":
                content_items.append(tool_output_item.text)
        if isinstance(tool_output_item, ImageContent):
            content_items.append(tool_output_item.model_dump_json())
        if isinstance(tool_output_item, EmbeddedResource):
            content_items.append(tool_output_item.model_dump_json())

    # Return the tool call result
    return ExtendedCallToolResult(
        id=tool_call.id,
        content=[
            TextContent(
                type="text",
                text="\n\n".join(content_items)
                if len(content_items) > 0
                else "[tool call successful, but no output, this may indicate empty file, directory, etc.]",
            ),
        ],
        metadata=metadata,
    )
