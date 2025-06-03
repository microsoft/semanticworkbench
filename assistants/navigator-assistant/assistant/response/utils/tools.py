from typing import Any, Awaitable, Callable

from assistant_extensions.mcp import (
    ExtendedCallToolRequestParams,
    MCPSession,
    retrieve_mcp_tools_and_sessions_from_sessions,
    execute_tool as execute_mcp_tool,
)
from attr import dataclass
from mcp import Tool as MCPTool
from mcp.types import TextContent
from openai.types.chat import ChatCompletionToolParam
from openai.types.shared_params import FunctionDefinition
from semantic_workbench_assistant.assistant_app import ConversationContext

from ...config import MCPToolsConfigModel


@dataclass
class ExecutableTool:
    name: str
    description: str
    parameters: dict[str, Any] | None
    func: Callable[[ConversationContext, dict[str, Any]], Awaitable[str]]

    def to_chat_completion_tool(self) -> ChatCompletionToolParam:
        """
        Convert the Tool instance to a format compatible with OpenAI's chat completion tools.
        """
        return ChatCompletionToolParam(
            type="function",
            function=FunctionDefinition(
                name=self.name,
                description=self.description,
                parameters=self.parameters or {},
            ),
        )


async def execute_tool(
    context: ConversationContext, tools: list[ExecutableTool], tool_name: str, arguments: dict[str, Any]
) -> str:
    """
    Execute a tool by its name with the provided arguments.
    """
    for tool in tools:
        if tool.name == tool_name:
            return await tool.func(context, arguments)

    return f"ERROR: Tool '{tool_name}' not found in the list of tools."


def get_tools_from_mcp_sessions(
    mcp_sessions: list[MCPSession], tools_config: MCPToolsConfigModel
) -> list[ExecutableTool]:
    """
    Retrieve the tools from the MCP sessions.
    """

    mcp_tools_and_sessions = retrieve_mcp_tools_and_sessions_from_sessions(
        mcp_sessions, tools_config.advanced.tools_disabled
    )
    return [convert_tool(session, tool) for tool, session in mcp_tools_and_sessions]


def convert_tool(mcp_session: MCPSession, mcp_tool: MCPTool) -> ExecutableTool:
    parameters = mcp_tool.inputSchema.copy()

    async def func(_: ConversationContext, arguments: dict[str, Any] | None = None) -> str:
        result = await execute_mcp_tool(
            mcp_session,
            ExtendedCallToolRequestParams(
                id=mcp_tool.name,
                name=mcp_tool.name,
                arguments=arguments,
            ),
            method_metadata_key="mcp_tool_call",
        )
        contents = []
        for content in result.content:
            match content:
                case TextContent():
                    contents.append(content.text)
        return "\n\n".join(contents)

    return ExecutableTool(
        name=mcp_tool.name,
        description=mcp_tool.description if mcp_tool.description else "[no description provided]",
        parameters=parameters,
        func=func,
    )
