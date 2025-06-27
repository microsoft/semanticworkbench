from typing import Iterable
from chat_context_toolkit.virtual_filesystem._types import ToolDefinition
from chat_context_toolkit.virtual_filesystem._virtual_filesystem import VirtualFileSystem
from openai.types.chat import ChatCompletionContentPartTextParam, ChatCompletionToolParam


class ViewTool(ToolDefinition):
    """Tool for viewing the contents of a file in the virtual file system."""

    def __init__(self, virtual_filesystem: VirtualFileSystem, tool_name: str = "view"):
        self.virtual_filesystem = virtual_filesystem
        self.tool_name = tool_name

    @property
    def tool_param(self) -> ChatCompletionToolParam:
        return ChatCompletionToolParam(
            type="function",
            function={
                "name": self.tool_name,
                "description": "Read the contents of a file at the specified path",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The path to the file to read (e.g., '/docs/file.txt')",
                        }
                    },
                    "required": ["path"],
                },
            },
        )

    async def execute(self, args: dict) -> str | Iterable[ChatCompletionContentPartTextParam]:
        """Execute the built-in view tool to read file contents."""
        path = args.get("path")
        if not path:
            return "Error: 'path' argument is required for the view tool"

        try:
            file_content = await self.virtual_filesystem.read_file(path)
        except FileNotFoundError:
            return f"Error: File at path {path} not found. Please pay attention to the available files and try again."

        result = f"<file path={path}>\n{file_content}\n</file>"
        return result
