"""Tests for the virtual file system."""

from datetime import datetime
from typing import Iterable

import pytest
from chat_context_toolkit.virtual_filesystem import (
    DirectoryEntry,
    FileEntry,
    MountPoint,
    VirtualFileSystem,
    WriteToolDefinition,
)
from openai.types.chat import (
    ChatCompletionMessageToolCallParam,
    ChatCompletionToolParam,
)


class SimpleFileSource:
    """Simple file source implementation for testing real VFS behavior."""

    def __init__(self, files: dict[str, str] | None = None, directories: dict[str, list[str]] | None = None):
        """Initialize with files and directories."""
        self.files = files or {}
        self.directories = directories or {}

    @property
    def write_tools(self) -> Iterable[WriteToolDefinition]:
        """Get write tools."""
        return []

    async def list_directory(self, path: str) -> Iterable[DirectoryEntry | FileEntry]:
        """List directory contents."""
        if path not in self.directories:
            raise FileNotFoundError(f"Directory not found: {path}")

        entries = []
        for item in self.directories[path]:
            if item.endswith("/"):
                dir_name = item.rstrip("/")
                dir_path = f"{path.rstrip('/')}/{dir_name}" if path != "/" else f"/{dir_name}"
                entries.append(DirectoryEntry(name=dir_name, path=dir_path))
            else:
                file_path = f"{path.rstrip('/')}/{item}" if path != "/" else f"/{item}"
                entries.append(
                    FileEntry(
                        filename=item,
                        path=file_path,
                        size=len(self.files.get(file_path, "")),
                        timestamp=datetime.now(),
                        permission="read",
                    )
                )
        return entries

    async def read_file(self, path: str) -> str:
        """Read file content."""
        if path not in self.files:
            raise FileNotFoundError(f"File not found: {path}")
        return self.files[path]


class TestVirtualFileSystem:
    """Tests for VirtualFileSystem behavior with real file sources."""

    async def test_list_with_no_mounts(self):
        """Test listing root directory with no mounts."""
        vfs = VirtualFileSystem()

        # Root directory should be empty
        result = list(await vfs.list_directory("/"))
        assert len(result) == 0

    async def test_mount_and_list_root_directory(self):
        """Test mounting file source and listing root shows mounted directories."""
        vfs = VirtualFileSystem()
        source = SimpleFileSource(directories={"/": ["file1.txt"]})

        vfs.mount(MountPoint(path="/docs", description="Test docs", file_source=source))

        # Root directory should show mounted paths
        result = list(await vfs.list_directory("/"))

        # Expected: should contain DirectoryEntry for "docs"
        assert len(result) == 1
        assert isinstance(result[0], DirectoryEntry)
        assert result[0].name == "docs"
        assert result[0].path == "/docs"

    async def test_duplicate_mount_raises_error(self):
        """Test mounting the same source multiple times."""
        vfs = VirtualFileSystem()
        source = SimpleFileSource(directories={"/": ["file1.txt"]})

        vfs.mount(MountPoint(path="/docs", description="Test docs", file_source=source))

        # Attempting to mount the same source again should raise an error
        with pytest.raises(ValueError, match="already mounted"):
            vfs.mount(MountPoint(path="/docs", description="Test docs", file_source=source))

    async def test_invalid_mount_paths_raise_error(self):
        """Test that mounting with invalid paths raises ValueError."""
        vfs = VirtualFileSystem()

        # Attempt to mount with invalid paths
        with pytest.raises(ValueError, match="is invalid"):
            vfs.mount(MountPoint(path="", description="Test", file_source=SimpleFileSource()))

        with pytest.raises(ValueError, match="is invalid"):
            vfs.mount(MountPoint(path="/", description="Test", file_source=SimpleFileSource()))

        with pytest.raises(ValueError, match="is invalid"):
            vfs.mount(MountPoint(path="docs", description="Test", file_source=SimpleFileSource()))

        with pytest.raises(ValueError, match="is invalid"):
            vfs.mount(MountPoint(path="/docs/sub-dir", description="Test", file_source=SimpleFileSource()))

        with pytest.raises(ValueError, match="is invalid"):
            vfs.mount(MountPoint(path="\\docs", description="Test", file_source=SimpleFileSource()))

    async def test_mount_and_list_mounted_directory_with_files(self):
        """Test listing files within a mounted directory."""
        vfs = VirtualFileSystem()
        source = SimpleFileSource(files={"/file1.txt": "content1"}, directories={"/": ["file1.txt"]})

        vfs.mount(MountPoint(path="/docs", description="Test docs", file_source=source))

        # List files in mounted directory
        result = list(await vfs.list_directory("/docs"))

        # Expected: should delegate to source and return file entries
        assert len(result) == 1
        assert isinstance(result[0], FileEntry)
        assert result[0].filename == "file1.txt"
        assert result[0].path == "/docs/file1.txt"

    async def test_mount_and_list_mounted_directory_with_sub_directories(self):
        """Test listing files within a mounted directory that contains sub-directories."""
        vfs = VirtualFileSystem()
        source = SimpleFileSource(
            files={"/file1.txt": "content1", "/subdir/file2.txt": "content2"},
            directories={"/": ["file1.txt", "subdir/"], "/subdir": ["file2.txt"]},
        )

        vfs.mount(MountPoint(path="/docs", description="Test docs", file_source=source))

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

    async def test_mount_and_list_sub_directory(self):
        """Test listing files within a mounted directory that contains sub-directories."""
        vfs = VirtualFileSystem()
        source = SimpleFileSource(
            files={"/file1.txt": "content1", "/subdir/file2.txt": "content2"},
            directories={"/": ["file1.txt", "subdir/"], "/subdir": ["file2.txt"]},
        )

        vfs.mount(MountPoint(path="/docs", description="Test docs", file_source=source))

        # List files in sub directory
        result = list(await vfs.list_directory("/docs/subdir"))

        # Expected: should delegate to source and return entries
        assert len(result) == 1
        assert isinstance(result[0], FileEntry)
        assert result[0].filename == "file2.txt"
        assert result[0].path == "/docs/subdir/file2.txt"

    async def test_list_non_existent_mount_raises_error(self):
        """Test reading from a non-existent mount raises FileNotFoundError."""
        vfs = VirtualFileSystem()

        # Attempt to read from a non-existent mount
        with pytest.raises(FileNotFoundError, match="Directory not found: /docs"):
            await vfs.list_directory("/docs")

        with pytest.raises(FileNotFoundError, match="Directory not found: /docs/nonexistent"):
            await vfs.list_directory("/docs/nonexistent")

    async def test_read_file_from_mounted_source(self):
        """Test reading file content from mounted source."""
        vfs = VirtualFileSystem()
        source = SimpleFileSource(files={"/file1.txt": "hello world"})

        vfs.mount(MountPoint(path="/docs", description="Test docs", file_source=source))

        # Read file from mounted source
        result = await vfs.read_file("/docs/file1.txt")

        # Expected: should delegate to source and return file content
        assert result == "hello world"

    async def test_multiple_mounts(self):
        """Test mounting multiple file sources at different paths."""
        vfs = VirtualFileSystem()

        docs_source = SimpleFileSource(files={"/readme.txt": "docs content"}, directories={"/": ["readme.txt"]})
        code_source = SimpleFileSource(files={"/main.py": "print('hello')"}, directories={"/": ["main.py"]})

        vfs.mount(MountPoint(path="/docs", description="Test docs", file_source=docs_source))
        vfs.mount(MountPoint(path="/src", description="Test source code", file_source=code_source))

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

    async def test_unmount_removes_access(self):
        """Test unmounting removes access to file source."""
        vfs = VirtualFileSystem()
        source = SimpleFileSource(files={"/file1.txt": "content"}, directories={"/": ["file1.txt"]})

        vfs.mount(MountPoint(path="/docs", description="Test docs", file_source=source))
        vfs.unmount("/docs")

        # After unmounting, directory should not be accessible
        with pytest.raises(FileNotFoundError):
            await vfs.list_directory("/docs")

    async def test_read_file_not_found_errors(self):
        """Test proper FileNotFoundError for non-existent paths."""
        vfs = VirtualFileSystem()
        source = SimpleFileSource(files={"/file1.txt": "content"}, directories={"/": ["file1.txt"]})
        vfs.mount(MountPoint(path="/docs", description="Test docs", file_source=source))

        # Non-existent file
        with pytest.raises(FileNotFoundError):
            await vfs.read_file("/nonexistent.txt")

        # Non-existent file
        with pytest.raises(FileNotFoundError):
            await vfs.read_file("/nonexistent.txt")

        # Non-existent file in mounted source
        with pytest.raises(FileNotFoundError):
            await vfs.read_file("/docs/nonexistent.txt")

    def test_tools_integration_with_mounted_sources(self):
        """Test that tools from mounted sources are available."""
        vfs = VirtualFileSystem()

        # Create a file source with write tools
        class SourceWithTools:
            @property
            def write_tools(self):
                return [MockWriteTool()]

            async def list_directory(self, path):
                return []

            async def read_file(self, path):
                return ""

        class MockWriteTool:
            @property
            def tool_param(self) -> ChatCompletionToolParam:
                return {
                    "type": "function",
                    "function": {"name": "write_file", "description": "Write content to a file"},
                }

            async def execute(self, args: dict) -> str:
                return "File written"

        # Initially no tools
        assert "write_file" not in vfs.tools

        # After mounting source with tools, they should be available
        source = SourceWithTools()
        vfs.mount(MountPoint(path="/docs", description="Test docs", file_source=source))

        # Tools should now include the mounted source's tools
        assert "write_file" in vfs.tools

    async def test_execute_nonexistent_tool_raises_error(self):
        """Test that executing a non-existent tool raises ValueError."""
        vfs = VirtualFileSystem()

        tool_call = ChatCompletionMessageToolCallParam(
            id="test", function={"name": "nonexistent_tool", "arguments": "{}"}, type="function"
        )

        # Non-existent tool should raise ValueError
        with pytest.raises(ValueError, match="Tool not found"):
            await vfs.execute_tool(tool_call)

    async def test_execute_tool_delegates_to_source(self):
        """Test that tool execution properly delegates to the appropriate mounted source."""
        vfs = VirtualFileSystem()

        # Create a file source with a write tool
        class SourceWithTool:
            @property
            def write_tools(self):
                return [TestWriteTool()]

            async def list_directory(self, path):
                return []

            async def read_file(self, path):
                return ""

        class TestWriteTool:
            @property
            def tool_param(self) -> ChatCompletionToolParam:
                return {
                    "type": "function",
                    "function": {"name": "test_write", "description": "Test write tool"},
                }

            async def execute(self, args: dict) -> str:
                return f"Tool executed with args: {args}"

        # Mount source with tool
        source = SourceWithTool()
        vfs.mount(MountPoint(path="/docs", description="Test docs", file_source=source))

        # Execute the tool
        tool_call = ChatCompletionMessageToolCallParam(
            id="test",
            function={"name": "test_write", "arguments": '{"content": "hello", "filename": "test.txt"}'},
            type="function",
        )

        result = await vfs.execute_tool(tool_call)

        # Should delegate to source and return result
        assert result == "Tool executed with args: {'content': 'hello', 'filename': 'test.txt'}"

    async def test_multiple_sources_with_tools(self):
        """Test that tools from multiple mounted sources are all available."""
        vfs = VirtualFileSystem()

        # Create two sources with different tools
        class SourceWithTool1:
            @property
            def write_tools(self):
                return [Tool1()]

            async def list_directory(self, path):
                return []

            async def read_file(self, path):
                return ""

        class SourceWithTool2:
            @property
            def write_tools(self):
                return [Tool2()]

            async def list_directory(self, path):
                return []

            async def read_file(self, path):
                return ""

        class Tool1:
            @property
            def tool_param(self) -> ChatCompletionToolParam:
                return {"type": "function", "function": {"name": "tool1", "description": "Tool 1"}}

            async def execute(self, args: dict) -> str:
                return "tool1 executed"

        class Tool2:
            @property
            def tool_param(self) -> ChatCompletionToolParam:
                return {"type": "function", "function": {"name": "tool2", "description": "Tool 2"}}

            async def execute(self, args: dict) -> str:
                return "tool2 executed"

        starting_tools_count = len(vfs.tools)

        # Mount both sources
        vfs.mount(MountPoint(path="/docs", description="Test docs", file_source=SourceWithTool1()))
        vfs.mount(MountPoint(path="/code", description="Test code", file_source=SourceWithTool2()))

        # Both tools should be available
        tools = vfs.tools
        assert len(tools) == starting_tools_count + 2
        assert "tool1" in tools
        assert "tool2" in tools

        # Both tools should be executable
        result1 = await vfs.execute_tool(
            ChatCompletionMessageToolCallParam(
                id="test1", function={"name": "tool1", "arguments": "{}"}, type="function"
            )
        )
        assert result1 == "tool1 executed"

        result2 = await vfs.execute_tool(
            ChatCompletionMessageToolCallParam(
                id="test2", function={"name": "tool2", "arguments": "{}"}, type="function"
            )
        )
        assert result2 == "tool2 executed"

    async def test_source_error_propagation(self):
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

        vfs.mount(MountPoint(path="/test", description="Test error source", file_source=ErrorSource()))

        # Source errors should propagate
        with pytest.raises(FileNotFoundError, match="Source-specific error"):
            await vfs.list_directory("/test/error")

        with pytest.raises(FileNotFoundError, match="File not found in source"):
            await vfs.read_file("/test/error.txt")

    async def test_unmount_removes_tools(self):
        """Test that unmounting a source removes its tools."""
        vfs = VirtualFileSystem()

        class SourceWithTool:
            @property
            def write_tools(self):
                return [TestTool()]

            async def list_directory(self, path):
                return []

            async def read_file(self, path):
                return ""

        class TestTool:
            @property
            def tool_param(self) -> ChatCompletionToolParam:
                return {"type": "function", "function": {"name": "test_tool", "description": "Test"}}

            async def execute(self, args: dict) -> str:
                return "executed"

        starting_tools_count = len(vfs.tools)

        # Mount source with tool
        vfs.mount(MountPoint(path="/docs", description="Test docs", file_source=SourceWithTool()))
        assert len(vfs.tools) == starting_tools_count + 1
        assert "test_tool" in vfs.tools

        # Unmount should remove tools
        vfs.unmount("/docs")
        assert len(vfs.tools) == starting_tools_count

        # Tool should no longer be executable
        with pytest.raises(ValueError, match="Tool not found"):
            await vfs.execute_tool(
                ChatCompletionMessageToolCallParam(
                    id="test", function={"name": "test_tool", "arguments": "{}"}, type="function"
                )
            )

    def test_builtin_ls_and_view_tools_available(self):
        """Test that VFS provides built-in ls and view tools."""
        vfs = VirtualFileSystem()

        # Built-in tools should be available even with no mounts
        tools = vfs.tools
        assert "ls" in tools
        assert "view" in tools

        # Tools should have proper definitions
        ls_tool = tools["ls"]
        assert ls_tool["type"] == "function"
        assert ls_tool["function"]["name"] == "ls"

        view_tool = tools["view"]
        assert view_tool["type"] == "function"
        assert view_tool["function"]["name"] == "view"

    async def test_builtin_ls_tool_lists_directory(self):
        """Test that the built-in ls tool can list directory contents."""
        vfs = VirtualFileSystem()

        # Create a source with mixed permissions and file types
        class TestFileSource:
            async def list_directory(self, path: str):
                if path == "/":
                    return [
                        FileEntry(
                            filename="writable-file.txt",
                            path="/writable-file.txt",
                            size=100,
                            timestamp=datetime.now(),
                            permission="read_write",
                        ),
                        FileEntry(
                            filename="readonly-file.txt",
                            path="/readonly-file.txt",
                            size=50,
                            timestamp=datetime.now(),
                            permission="read",
                        ),
                        DirectoryEntry(name="sub-dir-1", path="/sub-dir-1"),
                    ]
                elif path == "/sub-dir-1":
                    return [
                        FileEntry(
                            filename="nested-file.txt",
                            path="/sub-dir-1/nested-file.txt",
                            size=25,
                            timestamp=datetime.now(),
                            permission="read",
                        ),
                    ]
                else:
                    raise FileNotFoundError(f"Directory not found: {path}")

            async def read_file(self, path: str) -> str:
                return "file content"

            @property
            def write_tools(self):
                return []

        vfs.mount(MountPoint(path="/docs", description="Test docs", file_source=TestFileSource()))

        # Test ls on root (should show mounted directories)
        ls_call = ChatCompletionMessageToolCallParam(
            id="test", function={"name": "ls", "arguments": '{"path": "/"}'}, type="function"
        )
        result = await vfs.execute_tool(ls_call)
        assert isinstance(result, str)
        expected_root = "\n".join(["List of files in /:", "dr--    - docs/"])
        assert result == expected_root

        # Test ls on mounted directory
        ls_call = ChatCompletionMessageToolCallParam(
            id="test", function={"name": "ls", "arguments": '{"path": "/docs"}'}, type="function"
        )
        result = await vfs.execute_tool(ls_call)
        assert isinstance(result, str)
        expected = "\n".join([
            "List of files in /docs:",
            "dr--    - sub-dir-1/",
            "-r--  50B readonly-file.txt",
            "-rw- 100B writable-file.txt",
        ])
        assert result == expected

        # Test ls on subdirectory
        ls_call = ChatCompletionMessageToolCallParam(
            id="test", function={"name": "ls", "arguments": '{"path": "/docs/sub-dir-1"}'}, type="function"
        )
        result = await vfs.execute_tool(ls_call)
        assert isinstance(result, str)
        expected_nested = "\n".join(["List of files in /docs/sub-dir-1:", "-r--  25B nested-file.txt"])
        assert result == expected_nested

    async def test_builtin_view_tool_reads_file(self):
        """Test that the built-in view tool can read file contents."""
        vfs = VirtualFileSystem()
        source = SimpleFileSource(files={"/file1.txt": "Hello World", "/subdir/file2.txt": "Nested Content"})
        vfs.mount(MountPoint(path="/docs", description="Test docs", file_source=source))

        # Test view on file
        view_call = ChatCompletionMessageToolCallParam(
            id="test", function={"name": "view", "arguments": '{"path": "/docs/file1.txt"}'}, type="function"
        )
        result = await vfs.execute_tool(view_call)
        assert result == "Hello World"

        # Test view on nested file
        view_call = ChatCompletionMessageToolCallParam(
            id="test", function={"name": "view", "arguments": '{"path": "/docs/subdir/file2.txt"}'}, type="function"
        )
        result = await vfs.execute_tool(view_call)
        assert result == "Nested Content"

    async def test_builtin_tools_error_handling(self):
        """Test error handling for built-in ls and view tools."""
        vfs = VirtualFileSystem()

        # ls on non-existent path should raise error
        ls_call = ChatCompletionMessageToolCallParam(
            id="test", function={"name": "ls", "arguments": '{"path": "/nonexistent"}'}, type="function"
        )
        result = await vfs.execute_tool(ls_call)
        assert result == "Error: Directory not found: /nonexistent"

        # view on non-existent file should raise error
        view_call = ChatCompletionMessageToolCallParam(
            id="test", function={"name": "view", "arguments": '{"path": "/nonexistent.txt"}'}, type="function"
        )
        result = await vfs.execute_tool(view_call)
        assert result == "Error: File not found: /nonexistent.txt"

    def test_builtin_tools_combined_with_source_tools(self):
        """Test that built-in tools work alongside tools from mounted sources."""
        vfs = VirtualFileSystem()

        # Create source with custom tool
        class SourceWithTool:
            @property
            def write_tools(self):
                return [CustomTool()]

            async def list_directory(self, path):
                return []

            async def read_file(self, path):
                return ""

        class CustomTool:
            @property
            def tool_param(self) -> ChatCompletionToolParam:
                return {"type": "function", "function": {"name": "custom_tool", "description": "Custom tool"}}

            async def execute(self, args: dict) -> str:
                return "custom executed"

        vfs.mount(MountPoint(path="/docs", description="Test docs", file_source=SourceWithTool()))

        # Should have both built-in and source tools
        tools = vfs.tools
        assert "ls" in tools  # Built-in
        assert "view" in tools  # Built-in
        assert "custom_tool" in tools  # From source
        assert len(tools) == 3
