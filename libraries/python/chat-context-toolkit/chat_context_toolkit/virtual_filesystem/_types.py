"""Type definitions for the virtual file system."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Literal, Protocol

from openai.types.chat import (
    ChatCompletionContentPartTextParam,
    ChatCompletionToolParam,
)

logger = logging.getLogger("chat_context_toolkit.virtual_filesystem")


@dataclass
class DirectoryEntry:
    """Directory entry in the virtual file system."""

    path: str
    """Absolute path of the directory."""
    permission: Literal["read", "read_write"]
    """Permission for the directory - read_write means new files can be created in the directory."""
    description: str
    """Description of the directory, used for informing the LLM about the content."""

    @property
    def name(self) -> str:
        """Get the name of the directory from its path."""
        return self.path.rstrip("/").split("/")[-1] if self.path else ""


@dataclass
class FileEntry:
    """File entry in the virtual file system."""

    path: str
    """Absolute path of the file."""
    size: int
    """File size in bytes."""
    timestamp: datetime
    """Timestamp of the last modification."""
    permission: Literal["read", "read_write"]
    """Permission for the file"""
    description: str
    """Description of the file, used for informing the LLM about the content."""

    @property
    def filename(self) -> str:
        """Get the name of the file from its path."""
        return self.path.split("/")[-1] if self.path else ""


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


@dataclass
class MountPoint:
    """Mount point for a file source in the virtual file system."""

    entry: DirectoryEntry
    """The directory entry representing the mount point in the virtual file system."""

    file_source: FileSource
    """The file source that is mounted at the specified path."""
