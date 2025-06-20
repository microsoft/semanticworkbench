"""Type definitions for the virtual file system."""

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Literal, Protocol

from openai.types.chat import (
    ChatCompletionContentPartTextParam,
    ChatCompletionToolParam,
)


@dataclass
class DirectoryEntry:
    """Directory entry in the virtual file system."""

    name: str
    """Directory name"""
    path: str
    """Full path of the directory."""


@dataclass
class FileEntry:
    """File entry in the virtual file system."""

    filename: str
    """File name."""
    path: str
    """Full path of the file."""
    size: int
    """File size in bytes."""
    timestamp: datetime
    """Timestamp of the last modification."""
    permission: Literal["read", "read_write"]
    """Permission for the file"""


class WriteToolDefinition(Protocol):
    """Protocol for write tool definitions."""

    @property
    def tool_param(self) -> ChatCompletionToolParam:
        """Tool parameter definition for the write tool."""
        ...

    async def execute(self, args: dict) -> str | Iterable[ChatCompletionContentPartTextParam]:
        """Executes the tool with the given arguments."""
        ...


class FileSource(Protocol):
    """
    Protocol for file sources that can be mounted in the virtual file system.
    File sources can provide tools for writing files, and must implement methods for listing files and reading file contents.
    Paths provided to the FileSource will always be absolute, such as "/" or "/foo/bar", and will never include the mount point.
    For example, if a FileSource is mounted at "/foo", the path passed to the FileSource will be "/bar" for a path at "/foo/bar"
    in the virtual file system.
    """

    @property
    def write_tools(self) -> Iterable[WriteToolDefinition]:
        """Get the list of write tools provided by this file system provider."""
        ...

    async def list_directory(self, path: str) -> Iterable[DirectoryEntry | FileEntry]:
        """
        List files and directories at the specified path.
        Should support absolute paths only, such as "/dir/file.txt".
        If the directory does not exist, should raise FileNotFoundError.
        """
        ...

    async def read_file(self, path: str) -> str:
        """
        Read file content from the specified path.
        Should support absolute paths only, such as "/dir/file.txt".
        If the file does not exist, should raise FileNotFoundError.
        FileSource implementations are responsible for representing the file content as a string.
        """
        ...
