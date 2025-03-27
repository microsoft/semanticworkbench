# utils/tool_utils.py
import asyncio
import logging
from typing import Any, List

import deepmerge
from mcp import ServerSession, Tool
from mcp.server.fastmcp import Context
from mcp.types import CallToolResult
from openai.types.chat import (
    ChatCompletionToolParam,
)
from openai.types.shared_params import FunctionDefinition

from ._model import ToolCallFunction

logger = logging.getLogger(__name__)

MAX_RETRIES = 2


async def send_tool_call_progress(
    fastmcp_server_context: Context, message: str, data: dict[str, Any] | None = None
) -> None:
    """
    Sends a progress update message for a tool call to the FastMCP server. This is useful for providing
    real-time feedback to clients regarding task status.
    """

    server_session: ServerSession = fastmcp_server_context.session
    await server_session.send_log_message(
        level="info",
        data=message,
    )

    # FIXME: Would prefer to use this to send data via a custom notification, but it's not working
    # session: BaseSession = fastmcp_server_context.session
    # jsonrpc_notification = JSONRPCNotification(
    #     method="tool_call_progress",
    #     jsonrpc="2.0",
    #     params=ToolCallProgressMessage(
    #         message=message,
    #         data=data,
    #     ).model_dump(mode="json"),
    # )
    # await session._write_stream.send(JSONRPCMessage(jsonrpc_notification))


async def execute_tool_with_retries(tool_call_function, tool_name) -> CallToolResult:
    retries = 0
    while True:
        try:
            return await execute_tool(tool_call_function)
        except (TimeoutError, ConnectionError):
            if retries < MAX_RETRIES:
                logger.warning(f"Transient error in tool '{tool_name}', retrying... ({retries + 1}/{MAX_RETRIES})")
                retries += 1
                await asyncio.sleep(1)  # brief delay before retrying
            else:
                raise


async def execute_tool(
    tool_call_function: ToolCallFunction,
) -> CallToolResult:
    """
    Executes a tool call.

    Args:
        session: The MCP client session facilitating communication with the server.
        tool_call_function: The asynchronous tool call function to execute.

    Returns:
        The result of the tool call, typically wrapped as a protocol-compliant response.
    """

    result = await tool_call_function()
    return result


def convert_tools_to_openai_tools(
    mcp_tools: List[Tool] | None, extra_properties: dict[str, Any] | None = None
) -> List[ChatCompletionToolParam] | None:
    """
    Converts MCP tools into OpenAI-compatible tool schemas to facilitate interoperability.
    Extra properties can be appended to the generated schema, enabling richer descriptions
    or added functionality (e.g., custom fields for user context or explanations).
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
