# utils/tool_utils.py
import logging
from typing import List

import deepmerge
from mcp import Tool
from mcp.types import EmbeddedResource, ImageContent, TextContent

from .__model import MCPSession, ToolCall, ToolCallResult, ToolMessageType

logger = logging.getLogger(__name__)


def retrieve_tools_from_sessions(mcp_sessions: List[MCPSession]) -> List[Tool]:
    """
    Retrieve tools from all MCP sessions.
    """
    return [tool for mcp_session in mcp_sessions for tool in mcp_session.tools]


async def handle_tool_call(
    mcp_sessions: List[MCPSession],
    tool_call: ToolCall,
    method_metadata_key: str,
) -> ToolCallResult:
    """
    Handle the tool call by invoking the appropriate tool and returning a ToolCallResult.
    """

    # Initialize metadata
    metadata = {}

    # Find the tool and session from the full collection of sessions
    mcp_session, tool = next(
        (
            (mcp_session, tool)
            for mcp_session in mcp_sessions
            for tool in mcp_session.tools
            if tool.name == tool_call.name
        ),
        (None, None),
    )
    if not mcp_session or not tool:
        return ToolCallResult(
            id=tool_call.id,
            content=f"Tool '{tool_call.name}' not found in any of the sessions.",
            message_type=ToolMessageType.notice,
            metadata={},
        )

    # Update metadata with tool call details
    deepmerge.always_merger.merge(
        metadata,
        {
            "debug": {
                method_metadata_key: {
                    "tool_call": tool_call.to_json(),
                },
            },
        },
    )

    # Initialize tool_result
    tool_result = None
    tool_output: list[TextContent | ImageContent | EmbeddedResource] = []
    content_items: List[str] = []

    # Invoke the tool
    try:
        logger.debug(f"Invoking '{mcp_session.name}.{tool_call.name}' with arguments: {tool_call.arguments}")
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
