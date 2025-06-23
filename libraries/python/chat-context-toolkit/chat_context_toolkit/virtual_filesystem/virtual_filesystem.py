"""Virtual file system implementation."""

from typing import Iterable

from openai.types.chat import (
    ChatCompletionContentPartTextParam,
    ChatCompletionMessageToolCallParam,
    ChatCompletionToolParam,
)

from .types import DirectoryEntry, FileEntry, MountPoint


class VirtualFileSystem:
    """Virtual file system that can mount multiple file sources."""

    def __init__(self) -> None:
        """Initialize the virtual file system."""
        self._mounts: dict[str, MountPoint] = {}

    def mount(self, mount_point: MountPoint) -> None:
        """Mount a file source at the specified path."""
        path = mount_point.path

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
            return [DirectoryEntry(name=mount_path.lstrip("/"), path=mount_path) for mount_path in self._mounts.keys()]

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
                    adjusted_entries.append(DirectoryEntry(name=entry.name, path=mount_path + entry.path))

                case FileEntry():
                    adjusted_entries.append(
                        FileEntry(
                            filename=entry.filename,
                            path=mount_path + entry.path,
                            size=entry.size,
                            timestamp=entry.timestamp,
                            permission=entry.permission,
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
            f"{mount_path}: ({mount_point.description})" for mount_path, mount_point in self._mounts.items()
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

        # Parse arguments from tool call
        import json

        args = json.loads(tool_call["function"]["arguments"])

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

        # Format the output similar to Linux ls -l with header and name-only entries:
        # Directories are listed first, in alphabetical order and with a trailing slash.
        # Files are listed next, in alphabetical order, with permissions and size.
        # Example output:
        # List of files in /path:
        # dr--    - dirname/
        # -rw- 100B filename.txt
        # -r--  50B readonly.txt
        lines = [f"List of files in {path}:"]

        # Collect directory and file entries separately so we can sort them independently
        directory_names_and_lines = []
        file_names_and_lines = []

        for entry in entries:
            match entry:
                case DirectoryEntry():
                    # Directories use 'd' prefix, show 0B size, and add trailing /
                    directory_names_and_lines.append((entry.name, f"dr--    - {entry.name}/"))

                case FileEntry():
                    # Files show permissions and size with B suffix, just the filename
                    perms = "-rw-" if entry.permission == "read_write" else "-r--"
                    # Right-align size to 4 characters
                    size_str = f"{entry.size}B".rjust(4)
                    file_names_and_lines.append((entry.filename, f"{perms} {size_str} {entry.filename}"))

        if not directory_names_and_lines and not file_names_and_lines:
            directory_names_and_lines.append(("", "(empty directory)"))

        # Sort directories and files separately, then combine
        directory_names_and_lines = [entry[1] for entry in sorted(directory_names_and_lines, key=lambda x: x[0])]
        file_names_and_lines = [entry[1] for entry in sorted(file_names_and_lines, key=lambda x: x[0])]
        lines.extend(directory_names_and_lines)
        lines.extend(file_names_and_lines)

        return "\n".join(lines)

    async def _execute_view_tool(self, args: dict) -> str | Iterable[ChatCompletionContentPartTextParam]:
        """Execute the built-in view tool to read file contents."""
        path = args.get("path")
        if not path:
            return "Error: 'path' argument is required for the view tool"

        try:
            result = await self.read_file(path)
        except FileNotFoundError:
            return f"Error: File not found: {path}"

        return result
