"""Virtual file system implementation."""

from typing import Iterable

from openai.types.chat import (
    ChatCompletionContentPartTextParam,
)

from ._types import DirectoryEntry, FileEntry, MountPoint


class VirtualFileSystem:
    """Virtual file system that can mount multiple file sources."""

    def __init__(self, mounts: Iterable[MountPoint] = []) -> None:
        """Initialize the virtual file system."""
        self._mounts: dict[str, MountPoint] = {}
        for mount in mounts:
            self._mount(mount)

    def _mount(self, mount_point: MountPoint) -> None:
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

    @property
    def mounts(self) -> Iterable[MountPoint]:
        """Get the mounts of the virtual file system."""
        return self._mounts.values()

    def _split_path(self, path: str) -> tuple[str, str]:
        path_segments = path.split("/")
        if len(path_segments) < 2:
            raise ValueError(
                f"Invalid path format: {path}. Path must start with '/' and contain at least one directory."
            )

        _, mount_path_segment, *source_path_segments = path_segments
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
