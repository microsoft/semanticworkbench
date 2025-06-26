"""Virtual file system implementation."""

import json
from typing import Iterable

from openai.types.chat import (
    ChatCompletionContentPartTextParam,
    ChatCompletionMessageToolCallParam,
    ChatCompletionToolParam,
)

from ._types import DirectoryEntry, FileEntry, MountPoint, logger


class VirtualFileSystem:
    """Virtual file system that can mount multiple file sources."""

    def __init__(self, mounts: Iterable[MountPoint] = []) -> None:
        """Initialize the virtual file system."""
        self._mounts: dict[str, MountPoint] = {}
        for mount in mounts:
            self.mount(mount)

    def mount(self, mount_point: MountPoint) -> None:
        """Mount a file source at the specified path."""
        path = mount_point.entry.path

        # Validate mount path - assign conditions to variables for readability
        is_empty = not path
        is_root = path == "/"
        is_relative = not path.startswith("/") if path else False
        has_nested_path = "/" in path[1:] if path else False
        has_backslash = "\\" in path

        is_invalid_path = is_empty or is_root or is_relative or has_nested_path or has_backslash

        if is_invalid_path:
            raise ValueError(
                f"Mount path {path} is invalid. Path must be a single, absolute directory at the root, such as '/mount'."
            )

        if path in self._mounts:
            raise ValueError(f"Path {path} is already mounted")

        self._mounts[path] = mount_point

    def unmount(self, path: str) -> None:
        """Unmount the file source at the specified path."""
        if path not in self._mounts:
            raise ValueError(f"No mount found at path: {path}")
        del self._mounts[path]

    def _split_path(self, path: str) -> tuple[str, str]:
        _, mount_path_segment, *source_path_segments = path.split("/")
        mount_path = "/" + mount_path_segment
        source_path = "/" + "/".join(source_path_segments)
        return mount_path, source_path

    async def list_directory(self, path: str) -> Iterable[DirectoryEntry | FileEntry]:
        """
        List files and directories at the specified path.
        Directory paths that do not exist result in FileNotFoundError.
        """
        # Delegates to the appropriate FileSources as needed.
        # Requests for relative paths, such as "." or "foo" are considered invalid.
        # Requests for absolute paths are valid, such as "/", "/foo", or "/bar/baz".
        # Requests for the root path will return the DirectoryEntry for all mounts.

        if path == "/":
            # Return DirectoryEntry for each mount point
            return [
                DirectoryEntry(
                    path=mount_path,
                    description=mount_point.entry.description,
                    permission=mount_point.entry.permission,
                )
                for mount_path, mount_point in self._mounts.items()
            ]

        mount_path, source_path = self._split_path(path)

        if mount_path not in self._mounts:
            raise FileNotFoundError(f"Directory not found: {path}")

        source = self._mounts[mount_path].file_source
        source_entries = await source.list_directory(source_path)

        # Adjust paths to include mount prefix
        adjusted_entries: list[DirectoryEntry | FileEntry] = []
        for entry in source_entries:
            match entry:
                case DirectoryEntry():
                    adjusted_entries.append(
                        DirectoryEntry(
                            path=mount_path + entry.path,
                            description=entry.description,
                            permission=entry.permission,
                        )
                    )

                case FileEntry():
                    adjusted_entries.append(
                        FileEntry(
                            path=mount_path + entry.path,
                            size=entry.size,
                            timestamp=entry.timestamp,
                            permission=entry.permission,
                            description=entry.description,
                        )
                    )

        return adjusted_entries

    async def read_file(self, path: str) -> str | Iterable[ChatCompletionContentPartTextParam]:
        """
        Read file content from the specified path, delegating to the appropriate FileSource.
        File paths that do not exist result in FileNotFoundError.
        """

        # Split path to extract mount point and file path within mount
        mount_path, source_path = self._split_path(path)

        if mount_path not in self._mounts:
            raise FileNotFoundError(f"File not found: {path}")

        source = self._mounts[mount_path].file_source

        return await source.read_file(source_path)

    @property
    def tools(self) -> dict[str, ChatCompletionToolParam]:
        """
        Get the tools available in the virtual file system, to be used in chat-completions.
        Includes tools built-in to the virtual file system, as well as tools provided by mounted FileSources.
        """
        tools_dict = {}

        mount_list = "; ".join(
            f"{mount_path}: ({mount_point.entry.description})" for mount_path, mount_point in self._mounts.items()
        )

        # Add built-in VFS tools
        tools_dict["ls"] = {
            "type": "function",
            "function": {
                "name": "ls",
                "description": "List files and directories at the specified path. Root directories: " + mount_list,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The path to list (e.g., '/', '/docs', '/docs/subdir')",
                        }
                    },
                    "required": ["path"],
                },
            },
        }

        tools_dict["view"] = {
            "type": "function",
            "function": {
                "name": "view",
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
        }

        # Collect tools from all mounted sources
        for mount_point in self._mounts.values():
            for tool in mount_point.file_source.write_tools:
                tool_param = tool.tool_param
                tool_name = tool_param["function"]["name"]
                tools_dict[tool_name] = tool_param

        return tools_dict

    async def execute_tool(
        self, tool_call: ChatCompletionMessageToolCallParam
    ) -> str | Iterable[ChatCompletionContentPartTextParam]:
        """
        Execute a tool with the given name and arguments. For tools provided by FileSources, this will delegate to the appropriate FileSource.
        Calls to execute tools that do not exist result in ValueError.
        """
        tool_name = tool_call["function"]["name"]
        arguments_str = tool_call["function"]["arguments"]

        logger.info("executing tool; name: %s, arguments: %s", tool_name, arguments_str)

        # Parse arguments from tool call
        try:
            args = json.loads(arguments_str)
        except json.JSONDecodeError as e:
            return f"Error parsing tool arguments: {e}"

        # Handle built-in VFS tools
        match tool_name:
            case "ls":
                return await self._execute_ls_tool(args)
            case "view":
                return await self._execute_view_tool(args)

            case _:
                # Find the tool in mounted sources
                for mount_point in self._mounts.values():
                    for tool in mount_point.file_source.write_tools:
                        tool_param = tool.tool_param
                        if tool_param["function"]["name"] == tool_name:
                            return await tool.execute(args)

        # Tool not found
        raise ValueError(f"Tool not found: {tool_name}")

    async def _execute_ls_tool(self, args: dict) -> str:
        """Execute the built-in ls tool to list directory contents."""
        path = args.get("path")
        if not path:
            return "Error: 'path' argument is required for the ls tool"

        try:
            entries = await self.list_directory(path)
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

    async def _execute_view_tool(self, args: dict) -> str:
        """Execute the built-in view tool to read file contents."""
        path = args.get("path")
        if not path:
            return "Error: 'path' argument is required for the view tool"

        try:
            result = await self.read_file(path)
            result = f"<file path={path}>\n{result}\n</file>"
        except FileNotFoundError:
            return f"Error: File at path {path} not found. Please pay attention to the available files and try again."
        return result
