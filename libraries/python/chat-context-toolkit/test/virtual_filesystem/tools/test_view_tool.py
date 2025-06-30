from unittest.mock import MagicMock

from chat_context_toolkit.virtual_filesystem import VirtualFileSystem
from chat_context_toolkit.virtual_filesystem.tools import ViewTool


async def test_builtin_view_tool_reads_file():
    """Test that the built-in view tool can read file contents."""
    mock_vfs = MagicMock(spec=VirtualFileSystem)
    mock_vfs.read_file.return_value = "Hello World"

    # Test view on file
    view_tool = ViewTool(mock_vfs)
    result = await view_tool.execute({"path": "/docs/file1.txt"})

    mock_vfs.read_file.assert_called_once_with("/docs/file1.txt")
    assert result == '<file path="/docs/file1.txt">\nHello World\n</file>'


async def test_view_tool_error_handling():
    """Test error handling for built-in ls and view tools."""
    mock_vfs = MagicMock(spec=VirtualFileSystem)
    mock_vfs.read_file.side_effect = FileNotFoundError("File not found")

    # view on non-existent file should raise error
    view_tool = ViewTool(mock_vfs)
    result = await view_tool.execute({"path": "/nonexistent.txt"})
    assert (
        result
        == "Error: File at path /nonexistent.txt not found. Please pay attention to the available files and try again."
    )
