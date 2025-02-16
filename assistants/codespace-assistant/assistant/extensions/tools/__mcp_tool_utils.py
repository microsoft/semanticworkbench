# utils/tool_utils.py
import logging
from textwrap import dedent
from typing import AsyncGenerator, List

import deepmerge
from mcp import Tool
from mcp.types import EmbeddedResource, ImageContent, TextContent

from .__model import MCPSession, ToolCall, ToolCallResult, ToolMessageType, ToolsConfigModel

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


async def execute_tool_call(
    mcp_session: MCPSession,
    tool_call: ToolCall,
    method_metadata_key: str,
) -> ToolCallResult:

        # Initialize metadata
    metadata = {}

    # Initialize tool_result
    tool_result = None
    tool_output: list[TextContent | ImageContent | EmbeddedResource] = []
    content_items: List[str] = []

    # Invoke the tool
    try:
        logger.debug(f"Invoking '{mcp_session.config.key}.{tool_call.name}' with arguments: {tool_call.arguments}")
        tool_result = await mcp_session.client_session.call_tool(tool_call.name, tool_call.arguments)
        tool_output = tool_result.content
    except Exception as e:
        logger.exception(f"Error executing tool '{tool_call.name}': {e}")
        content_items.append(f"An error occurred while executing the tool '{tool_call.to_json()}': {e}")

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

async def handle_tool_call(
    mcp_sessions: List[MCPSession],
    tool_call: ToolCall,
    method_metadata_key: str,
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

    return await execute_tool_call(mcp_session, tool_call, method_metadata_key)


async def handle_long_running_tool_call(
    mcp_sessions: List[MCPSession],
    tool_call: ToolCall,
    method_metadata_key: str,
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
    tool_call_result = await execute_tool_call(mcp_session, tool_call, method_metadata_key)
    yield tool_call_result
