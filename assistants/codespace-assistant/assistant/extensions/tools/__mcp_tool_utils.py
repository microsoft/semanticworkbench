# utils/tool_utils.py
import logging
from typing import List

import deepmerge
from mcp import ClientSession, Tool
from mcp.types import TextContent

from .__model import ToolCall, ToolCallResult, ToolMessageType

logger = logging.getLogger(__name__)


async def retrieve_tools_from_sessions(sessions: List[ClientSession]) -> List[Tool]:
    """
    Retrieve tools from all MCP sessions.
    """
    all_tools: List[Tool] = []
    for session in sessions:
        try:
            tools_response = await session.list_tools()
            tools = tools_response.tools
            all_tools.extend(tools)
            logger.debug(f"Retrieved tools from session: {[tool.name for tool in tools]}")
        except Exception as e:
            logger.exception(f"Error retrieving tools from session: {e}")
    return all_tools


async def handle_tool_call(
    sessions: List[ClientSession],
    tool_call: ToolCall,
    all_mcp_tools: List[Tool],
    method_metadata_key: str,
) -> ToolCallResult:
    """
    Handle the tool call by invoking the appropriate tool and returning a ToolCallResult.
    """

    metadata = {}

    tool = next((t for t in all_mcp_tools if t.name == tool_call.name), None)
    if not tool:
        return ToolCallResult(
            id=tool_call.id,
            content=f"Tool '{tool_call.name}' not found.",
            message_type=ToolMessageType.notice,
            metadata={},
        )

    target_session = next(
        (session for session in sessions if tool_call.name in [tool.name for tool in all_mcp_tools]), None
    )

    if not target_session:
        raise ValueError(f"Tool '{tool_call.name}' not found in any of the sessions.")

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

    # Invoke the tool
    try:
        logger.debug(f"Invoking tool '{tool_call.name}' with arguments: {tool_call.arguments}")
        tool_result = await target_session.call_tool(tool_call.name, tool_call.arguments)
        tool_output = tool_result.content[0] if tool_result.content else ""
    except Exception as e:
        logger.exception(f"Error executing tool '{tool_call.name}': {e}")
        tool_output = f"An error occurred while executing the tool '{tool_call.to_json()}': {e}"

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

    # Return the tool call result
    content: str | None = None
    if isinstance(tool_output, str):
        content = tool_output

    if isinstance(tool_output, TextContent):
        content = tool_output.text

    # Return the tool call result
    return ToolCallResult(
        id=tool_call.id,
        content=content or "Error executing tool, unsupported output type.",
        message_type=ToolMessageType.tool_result,
        metadata=metadata,
    )
