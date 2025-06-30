from dataclasses import dataclass
from typing import Iterable

from openai.types.chat import ChatCompletionContentPartTextParam, ChatCompletionToolParam

from chat_context_toolkit.virtual_filesystem._types import DirectoryEntry, FileEntry, ToolDefinition
from chat_context_toolkit.virtual_filesystem._virtual_filesystem import VirtualFileSystem


@dataclass
class LsToolOptions:
    tool_name: str = "ls"
    """Name of the tool provided to the LLM."""
    tool_description: str = "List files and directories at the specified path. Root directories: {root_path_list}"
    """Description of the tool provided to the LLM."""
    path_argument_description: str = "The path to list (e.g., '/', '/docs', '/docs/subdir)"
    """Description of the 'path' argument."""


class LsTool(ToolDefinition):
    """Tool for listing files and directories in the virtual file system."""

    def __init__(self, virtual_filesystem: VirtualFileSystem, options: LsToolOptions = LsToolOptions()) -> None:
        self.virtual_filesystem = virtual_filesystem
        self.options = options

    @property
    def tool_param(self) -> ChatCompletionToolParam:
        mount_list = "; ".join(
            f"{mount_point.entry.path}: ({mount_point.entry.description})"
            for mount_point in self.virtual_filesystem.mounts
        )
        return ChatCompletionToolParam(
            type="function",
            function={
                "name": self.options.tool_name,
                "description": self.options.tool_description.format(root_path_list=mount_list),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": self.options.path_argument_description.format(root_path_list=mount_list),
                        }
                    },
                    "required": ["path"],
                },
            },
        )

    async def execute(self, args: dict) -> str | Iterable[ChatCompletionContentPartTextParam]:
        """Execute the built-in ls tool to list directory contents."""
        path = args.get("path")
        if not path:
            return f"Error: 'path' argument is required for the {self.options.tool_name} tool"

        try:
            entries = await self.virtual_filesystem.list_directory(path)
        except FileNotFoundError:
            return f"Error: Directory not found: {path}"

        # Collect directory and file entries separately so we can sort them independently
        directory_names_and_lines: list[tuple[str, str]] = []
        file_names_and_lines: list[tuple[str, str]] = []

        def format_ls_line(directory: bool, writeable: bool, path: str, size: str, description: str) -> str:
            # Format the output similar to Linux ls -l with header and name-only entries:
            # Directories are listed first, in alphabetical order and with a trailing slash.
            # Files are listed next, in alphabetical order, with permissions and size.
            # Example output:
            # List of files in /path:
            # dr-    - dirname/ - description of directory
            # -rw 100B filename.txt - description of file
            # -r-  50B readonly.txt - description of file
            dir_flag = "d" if directory else "-"
            read_flag = "r"  # all entries are considered readable
            write_flag = "w" if writeable else "-"
            executable_flag = "-"  # no execute permissions at the moment
            perms = f"{dir_flag}{read_flag}{write_flag}{executable_flag}"
            name = path.split("/")[-1]  # Get the last part of the path
            name += "/" if directory and not name.endswith("/") else ""
            return f"{perms} {size.rjust(4)} {name} - {description}"

        for entry in entries:
            match entry:
                case DirectoryEntry():
                    directory_names_and_lines.append((
                        entry.path,
                        format_ls_line(
                            directory=True,
                            writeable=entry.permission == "read_write",
                            path=entry.path,
                            size="-",
                            description=entry.description,
                        ),
                    ))

                case FileEntry():
                    file_names_and_lines.append((
                        entry.path,
                        format_ls_line(
                            directory=False,
                            writeable=entry.permission == "read_write",
                            path=entry.path,
                            size=f"{entry.size}B",
                            description=entry.description,
                        ),
                    ))

        if not directory_names_and_lines and not file_names_and_lines:
            directory_names_and_lines.append(("", "(empty directory)"))

        # Sort directories and files separately, then combine
        directory_lines = [entry[1] for entry in sorted(directory_names_and_lines, key=lambda x: x[0])]
        file_lines = [entry[1] for entry in sorted(file_names_and_lines, key=lambda x: x[0])]
        lines = [f"List of files in {path}:", *directory_lines, *file_lines]

        return "\n".join(lines)
