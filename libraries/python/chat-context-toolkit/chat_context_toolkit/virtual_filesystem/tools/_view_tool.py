from dataclasses import dataclass
from typing import Iterable

from openai.types.chat import ChatCompletionContentPartTextParam, ChatCompletionToolParam

from chat_context_toolkit.virtual_filesystem._types import ToolDefinition
from chat_context_toolkit.virtual_filesystem._virtual_filesystem import VirtualFileSystem


@dataclass
class ViewToolOptions:
    tool_name: str = "view"
    """Name of the tool provided to the LLM."""
    tool_description: str = "Read the contents of a file at the specified path"
    """Description of the tool provided to the LLM."""
    path_argument_description: str = "The path to the file to read (e.g., '/docs/file.txt')"
    """Description of the 'path' argument."""


class ViewTool(ToolDefinition):
    """Tool for viewing the contents of a file in the virtual file system."""

    def __init__(self, virtual_filesystem: VirtualFileSystem, options: ViewToolOptions = ViewToolOptions()) -> None:
        self.virtual_filesystem = virtual_filesystem
        self.options = options

    @property
    def tool_param(self) -> ChatCompletionToolParam:
        return ChatCompletionToolParam(
            type="function",
            function={
                "name": self.options.tool_name,
                "description": self.options.tool_description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": self.options.path_argument_description,
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
            return f"Error: 'path' argument is required for the {self.options.tool_name} tool"

        try:
            file_content = await self.virtual_filesystem.read_file(path)
        except FileNotFoundError:
            return f"Error: File at path {path} not found. Please pay attention to the available files and try again."
        except ValueError as e:
            return f"Error: {str(e)}"

        result = f'<file path="{path}">\n{file_content}\n</file>'
        return result
