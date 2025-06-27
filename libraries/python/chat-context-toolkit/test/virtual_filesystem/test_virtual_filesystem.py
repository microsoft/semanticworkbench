"""Tests for the virtual file system."""

from datetime import datetime
from typing import Iterable

import pytest
from chat_context_toolkit.virtual_filesystem import (
    DirectoryEntry,
    FileEntry,
    MountPoint,
    VirtualFileSystem,
)


class MockFileSource:
    """Simple file source implementation for testing VFS behavior."""

    def __init__(self, files: dict[str, str] | None = None, directories: dict[str, list[str]] | None = None):
        """Initialize with files and directories."""
        self.files = files or {}
        self.directories = directories or {}

    async def list_directory(self, path: str) -> Iterable[DirectoryEntry | FileEntry]:
        """List directory contents."""
        if path not in self.directories:
            raise FileNotFoundError(f"Directory not found: {path}")

        entries = []
        for item in self.directories[path]:
            if item.endswith("/"):
                dir_name = item.rstrip("/")
                dir_path = f"{path.rstrip('/')}/{dir_name}" if path != "/" else f"/{dir_name}"
                entries.append(
                    DirectoryEntry(path=dir_path, description=f"Directory {dir_name} in {path}", permission="read")
                )
            else:
                file_path = f"{path.rstrip('/')}/{item}" if path != "/" else f"/{item}"
                entries.append(
                    FileEntry(
                        path=file_path,
                        size=len(self.files.get(file_path, "")),
                        timestamp=datetime.now(),
                        permission="read",
                        description=f"File {item} in {path}",
                    )
                )
        return entries

    async def read_file(self, path: str) -> str:
        """Read file content."""
        if path not in self.files:
            raise FileNotFoundError(f"File not found: {path}")
        return self.files[path]


async def test_list_with_no_mounts():
    """Test listing root directory with no mounts."""
    vfs = VirtualFileSystem()

    # Root directory should be empty
    result = list(await vfs.list_directory("/"))
    assert len(result) == 0


async def test_mount_and_list_root_directory():
    """Test mounting file source and listing root shows mounted directories."""
    source = MockFileSource(directories={"/": ["file1.txt"]})

    vfs = VirtualFileSystem(
        mounts=[
            MountPoint(
                entry=DirectoryEntry(path="/docs", description="Test docs", permission="read"),
                file_source=source,
            )
        ]
    )

    # Root directory should show mounted paths
    result = list(await vfs.list_directory("/"))

    # Expected: should contain DirectoryEntry for "docs"
    assert len(result) == 1
    assert isinstance(result[0], DirectoryEntry)
    assert result[0].path == "/docs"


async def test_duplicate_mount_raises_error():
    """Test mounting the same source multiple times."""
    source = MockFileSource(directories={"/": ["file1.txt"]})

    vfs = VirtualFileSystem(
        mounts=[
            MountPoint(
                entry=DirectoryEntry(path="/docs", description="Test docs", permission="read"),
                file_source=source,
            )
        ]
    )

    # Attempting to mount the same source again should raise an error
    with pytest.raises(ValueError, match="already mounted"):
        vfs._mount(
            MountPoint(
                entry=DirectoryEntry(path="/docs", description="Test docs", permission="read"),
                file_source=source,
            )
        )


async def test_invalid_mount_paths_raise_error():
    """Test that mounting with invalid paths raises ValueError."""

    # Attempt to mount with invalid paths
    with pytest.raises(ValueError, match="is invalid"):
        VirtualFileSystem(
            mounts=[
                MountPoint(
                    entry=DirectoryEntry(path="", description="Test", permission="read"),
                    file_source=MockFileSource(),
                )
            ]
        )

    with pytest.raises(ValueError, match="is invalid"):
        VirtualFileSystem(
            mounts=[
                MountPoint(
                    entry=DirectoryEntry(path="/", description="Test", permission="read"),
                    file_source=MockFileSource(),
                )
            ]
        )

    with pytest.raises(ValueError, match="is invalid"):
        VirtualFileSystem(
            mounts=[
                MountPoint(
                    entry=DirectoryEntry(path="docs", description="Test", permission="read"),
                    file_source=MockFileSource(),
                )
            ]
        )

    with pytest.raises(ValueError, match="is invalid"):
        VirtualFileSystem(
            mounts=[
                MountPoint(
                    entry=DirectoryEntry(path="/docs/sub-dir", description="Test", permission="read"),
                    file_source=MockFileSource(),
                )
            ]
        )

    with pytest.raises(ValueError, match="is invalid"):
        VirtualFileSystem(
            mounts=[
                MountPoint(
                    entry=DirectoryEntry(path="\\docs", description="Test", permission="read"),
                    file_source=MockFileSource(),
                )
            ]
        )


async def test_mount_and_list_mounted_directory_with_files():
    """Test listing files within a mounted directory."""
    vfs = VirtualFileSystem()
    source = MockFileSource(files={"/file1.txt": "content1"}, directories={"/": ["file1.txt"]})

    vfs._mount(
        MountPoint(
            entry=DirectoryEntry(path="/docs", description="Test docs", permission="read"),
            file_source=source,
        )
    )

    # List files in mounted directory
    result = list(await vfs.list_directory("/docs"))

    # Expected: should delegate to source and return file entries
    assert len(result) == 1
    assert isinstance(result[0], FileEntry)
    assert result[0].path == "/docs/file1.txt"


async def test_mount_and_list_mounted_directory_with_sub_directories():
    """Test listing files within a mounted directory that contains sub-directories."""
    vfs = VirtualFileSystem()
    source = MockFileSource(
        files={"/file1.txt": "content1", "/subdir/file2.txt": "content2"},
        directories={"/": ["file1.txt", "subdir/"], "/subdir": ["file2.txt"]},
    )

    vfs._mount(
        MountPoint(
            entry=DirectoryEntry(path="/docs", description="Test docs", permission="read"),
            file_source=source,
        )
    )

    # List files in mounted directory
    result = list(await vfs.list_directory("/docs"))

    # Expected: should delegate to source and return entries
    assert len(result) == 2
    assert isinstance(result[0], FileEntry)
    assert result[0].filename == "file1.txt"
    assert result[0].path == "/docs/file1.txt"
    assert isinstance(result[1], DirectoryEntry)
    assert result[1].name == "subdir"
    assert result[1].path == "/docs/subdir"


async def test_mount_and_list_sub_directory():
    """Test listing files within a mounted directory that contains sub-directories."""
    vfs = VirtualFileSystem()
    source = MockFileSource(
        files={"/file1.txt": "content1", "/subdir/file2.txt": "content2"},
        directories={"/": ["file1.txt", "subdir/"], "/subdir": ["file2.txt"]},
    )

    vfs._mount(
        MountPoint(
            entry=DirectoryEntry(path="/docs", description="Test docs", permission="read"),
            file_source=source,
        )
    )

    # List files in sub directory
    result = list(await vfs.list_directory("/docs/subdir"))

    # Expected: should delegate to source and return entries
    assert len(result) == 1
    assert isinstance(result[0], FileEntry)
    assert result[0].filename == "file2.txt"
    assert result[0].path == "/docs/subdir/file2.txt"


async def test_list_non_existent_mount_raises_error():
    """Test reading from a non-existent mount raises FileNotFoundError."""
    vfs = VirtualFileSystem()

    # Attempt to read from a non-existent mount
    with pytest.raises(FileNotFoundError, match="Directory not found: /docs"):
        await vfs.list_directory("/docs")

    with pytest.raises(FileNotFoundError, match="Directory not found: /docs/nonexistent"):
        await vfs.list_directory("/docs/nonexistent")


async def test_read_file_from_mounted_source():
    """Test reading file content from mounted source."""
    vfs = VirtualFileSystem()
    source = MockFileSource(files={"/file1.txt": "hello world"})

    vfs._mount(
        MountPoint(
            entry=DirectoryEntry(path="/docs", description="Test docs", permission="read"),
            file_source=source,
        )
    )

    # Read file from mounted source
    result = await vfs.read_file("/docs/file1.txt")

    # Expected: should delegate to source and return file content
    assert result == "hello world"


async def test_multiple_mounts():
    """Test mounting multiple file sources at different paths."""
    vfs = VirtualFileSystem()

    docs_source = MockFileSource(files={"/readme.txt": "docs content"}, directories={"/": ["readme.txt"]})
    code_source = MockFileSource(files={"/main.py": "print('hello')"}, directories={"/": ["main.py"]})

    vfs._mount(
        MountPoint(
            entry=DirectoryEntry(path="/docs", description="Test docs", permission="read"),
            file_source=docs_source,
        )
    )
    vfs._mount(
        MountPoint(
            entry=DirectoryEntry(path="/src", description="Test source code", permission="read"),
            file_source=code_source,
        )
    )

    # Root should show both mounts
    root_result = list(await vfs.list_directory("/"))
    mount_names = {entry.name for entry in root_result if isinstance(entry, DirectoryEntry)}
    mount_paths = {entry.path for entry in root_result if isinstance(entry, DirectoryEntry)}
    assert "docs" in mount_names
    assert "src" in mount_names
    assert "/docs" in mount_paths
    assert "/src" in mount_paths

    # Each mount should show its files
    docs_result = list(await vfs.list_directory("/docs"))
    assert len(docs_result) == 1
    assert isinstance(docs_result[0], FileEntry)
    assert docs_result[0].filename == "readme.txt"
    assert docs_result[0].path == "/docs/readme.txt"

    src_result = list(await vfs.list_directory("/src"))
    assert len(src_result) == 1
    assert isinstance(src_result[0], FileEntry)
    assert src_result[0].filename == "main.py"
    assert src_result[0].path == "/src/main.py"


async def test_read_file_not_found_errors():
    """Test proper FileNotFoundError for non-existent paths."""
    vfs = VirtualFileSystem()
    source = MockFileSource(files={"/file1.txt": "content"}, directories={"/": ["file1.txt"]})
    vfs._mount(
        MountPoint(
            entry=DirectoryEntry(path="/docs", description="Test docs", permission="read"),
            file_source=source,
        )
    )

    # Non-existent file
    with pytest.raises(FileNotFoundError):
        await vfs.read_file("/nonexistent.txt")

    # Non-existent file
    with pytest.raises(FileNotFoundError):
        await vfs.read_file("/nonexistent.txt")

    # Non-existent file in mounted source
    with pytest.raises(FileNotFoundError):
        await vfs.read_file("/docs/nonexistent.txt")


async def test_source_error_propagation():
    """Test that errors from FileSource are properly propagated."""
    vfs = VirtualFileSystem()

    class ErrorSource:
        @property
        def write_tools(self):
            return []

        async def list_directory(self, path):
            if path == "/error":
                raise FileNotFoundError("Source-specific error")
            return []

        async def read_file(self, path):
            if path == "/error.txt":
                raise FileNotFoundError("File not found in source")
            return "content"

    vfs._mount(
        MountPoint(
            entry=DirectoryEntry(path="/test", description="Test error source", permission="read"),
            file_source=ErrorSource(),
        )
    )

    # Source errors should propagate
    with pytest.raises(FileNotFoundError, match="Source-specific error"):
        await vfs.list_directory("/test/error")

    with pytest.raises(FileNotFoundError, match="File not found in source"):
        await vfs.read_file("/test/error.txt")
