import json
from typing import Iterable

from openai.types.chat import ChatCompletionContentPartTextParam, ChatCompletionMessageToolCallParam

from chat_context_toolkit.virtual_filesystem._types import ToolDefinition


class ToolCollection(list[ToolDefinition]):
    def __init__(self, tools: Iterable[ToolDefinition]):
        super().__init__(tools)

    def has_tool(self, tool_name: str) -> bool:
        return self.get_tool(tool_name) is not None

    def get_tool(self, tool_name: str) -> ToolDefinition | None:
        for tool in self:
            if tool.tool_param["function"]["name"] == tool_name:
                return tool
        return None

    async def execute_tool(
        self, tool_call: ChatCompletionMessageToolCallParam
    ) -> str | Iterable[ChatCompletionContentPartTextParam]:
        """Execute a tool with the given name and arguments."""

        tool_name = tool_call["function"]["name"]

        tool_definition = self.get_tool(tool_name)
        if tool_definition is None:
            raise ValueError(f"Tool not found: {tool_name}")

        try:
            args = json.loads(tool_call["function"]["arguments"])
        except json.JSONDecodeError:
            return f"Error: Invalid JSON arguments: {tool_call['function']['arguments']}"

        return await tool_definition.execute(args)


def tool_result_to_string(tool_result: str | Iterable[ChatCompletionContentPartTextParam]) -> str:
    match tool_result:
        case str():
            return tool_result
        case Iterable():
            return "\n".join(part["text"] for part in tool_result)
