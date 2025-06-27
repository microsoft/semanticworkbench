from datetime import datetime
from unittest.mock import MagicMock

from chat_context_toolkit.virtual_filesystem import DirectoryEntry, FileEntry, VirtualFileSystem
from chat_context_toolkit.virtual_filesystem.tools import LsTool


async def test_ls_tool_lists_directory():
    """Test that the built-in ls tool can list directory contents."""

    mock_vfs = MagicMock(spec=VirtualFileSystem)

    async def list_directory(path: str) -> list[DirectoryEntry | FileEntry]:
        match path:
            case "/":
                return [
                    DirectoryEntry(
                        path="/docs",
                        description="Test docs",
                        permission="read",
                    ),
                ]
            case "/docs":
                return [
                    DirectoryEntry(
                        path="/sub-dir-1",
                        description="A sub-directory",
                        permission="read",
                    ),
                    FileEntry(
                        path="/writable-file.txt",
                        size=100,
                        timestamp=datetime.now(),
                        permission="read_write",
                        description="A writable file",
                    ),
                    FileEntry(
                        path="/readonly-file.txt",
                        size=50,
                        timestamp=datetime.now(),
                        permission="read",
                        description="A read-only file",
                    ),
                ]
            case "/docs/sub-dir-1":
                return [
                    FileEntry(
                        path="/docs/sub-dir-1/nested-file.txt",
                        size=25,
                        timestamp=datetime.now(),
                        permission="read",
                        description="A nested file",
                    ),
                ]
            case _:
                raise FileNotFoundError(f"Directory not found: {path}")

    mock_vfs.list_directory.side_effect = list_directory

    mock_vfs.read_file.return_value = "file content"

    ls_tool = LsTool(mock_vfs)

    # Test ls on root (should show mounted directories)
    result = await ls_tool.execute({"path": "/"})
    assert isinstance(result, str)
    expected_root = "\n".join(["List of files in /:", "dr--    - docs/ - Test docs"])
    assert result == expected_root

    # Test ls on mounted directory
    result = await ls_tool.execute({"path": "/docs"})
    assert isinstance(result, str)
    expected = "\n".join([
        "List of files in /docs:",
        "dr--    - sub-dir-1/ - A sub-directory",
        "-r--  50B readonly-file.txt - A read-only file",
        "-rw- 100B writable-file.txt - A writable file",
    ])
    assert result == expected

    # Test ls on subdirectory
    result = await ls_tool.execute({"path": "/docs/sub-dir-1"})
    assert isinstance(result, str)
    expected_nested = "\n".join(["List of files in /docs/sub-dir-1:", "-r--  25B nested-file.txt - A nested file"])
    assert result == expected_nested


async def test_ls_tool_error_handling():
    """Test error handling for built-in ls and view tools."""
    mock_vfs = MagicMock(spec=VirtualFileSystem)
    mock_vfs.list_directory.side_effect = FileNotFoundError("Directory not found")
    ls_tool = LsTool(mock_vfs)

    # ls on non-existent path should raise error
    result = await ls_tool.execute({"path": "/nonexistent"})
    assert result == "Error: Directory not found: /nonexistent"
