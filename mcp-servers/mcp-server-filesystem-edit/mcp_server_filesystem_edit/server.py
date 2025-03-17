# Copyright (c) Microsoft. All rights reserved.

import sys
from pathlib import Path
from typing import Literal

from mcp.server.fastmcp import Context, FastMCP

from mcp_server_filesystem_edit import settings
from mcp_server_filesystem_edit.tools.edit import CommonEdit
from mcp_server_filesystem_edit.types import EditRequest

# Set the name of the MCP server
server_name = "Filesystem Edit MCP Server"


async def get_allowed_directories(ctx: Context) -> list[Path]:
    """
    Helper function to get allowed directories from settings
    """
    if settings.allowed_directories:
        return [Path(directory).resolve() for directory in settings.allowed_directories]

    list_roots_result = await ctx.session.list_roots()
    if list_roots_result.roots:
        if sys.platform.startswith("win"):
            return [Path(root.uri.path.lstrip("/")).resolve() for root in list_roots_result.roots if root.uri.path]

        return [Path(root.uri.path).resolve() for root in list_roots_result.roots if root.uri.path]

    raise ValueError("No allowed_directories have been configured and no roots have been set.")


async def validate_path(ctx: Context, requested_path: str) -> Path:
    """
    Helper function to validate paths against allowed directories
    """
    allowed_dirs = await get_allowed_directories(ctx)

    if not allowed_dirs:
        raise PermissionError("No allowed_directories have been configured")

    if requested_path == ".":
        requested_path = str(allowed_dirs[0])

    absolute_path = Path(requested_path).resolve()
    for allowed_dir in allowed_dirs:
        if str(absolute_path).startswith(str(allowed_dir)):
            return absolute_path
    raise PermissionError(f"Access denied: {requested_path} is outside allowed_directories: {allowed_dirs}")


async def read_file(ctx: Context, path: str) -> str:
    """
    Reads the content of a file specified by the path.

    Args:
        path: The absolute or relative path to the file.

    Returns:
        The content of the file as a string.
    """
    file = await validate_path(ctx, path)

    if not file.exists() or not file.is_file():
        raise FileNotFoundError(f"File does not exist at path: {path}")

    try:
        return file.read_text(encoding="utf-8")
    except Exception as e:
        raise RuntimeError(f"Failed to read the file at {path}: {str(e)}")


async def write_file(ctx: Context, path: str, content: str) -> str:
    """
    Writes content to a file specified by the path. Creates the file if it does not exist.

    Args:
        path: The absolute or relative path to the file.
        content: The string content to write into the file.

    Returns:
        A confirmation message.
    """
    file = await validate_path(ctx, path)
    try:
        file.parent.mkdir(parents=True, exist_ok=True)  # Ensure parent directories exist
        file.write_text(content, encoding="utf-8")
        return f"Successfully wrote content to {path}"
    except Exception as e:
        raise RuntimeError(f"Failed to write to the file at {path}: {str(e)}")


def create_mcp_server() -> FastMCP:
    mcp = FastMCP(name=server_name, log_level=settings.log_level)

    @mcp.tool()
    async def view(ctx: Context, path: str) -> str:
        """
        Reads the content of a file specified by the path.

        Args:
            path: The absolute or relative path to the file.

        Returns:
            The content of the file as a string.
        """
        file_content = await read_file(ctx, path)
        return file_content

    @mcp.tool()
    async def edit_file(ctx: Context, path: str, task: str) -> str:
        """
        The user has a file editor corresponding to the file type, open like VSCode or TeXworks, open side by side with this chat.
        Use this tool when you need to make changes to that file or you want to create a new file (provide a new file path).
        Provide it a task that you want it to do in the document. For example, if you want to have it expand on one section,
        you can say "expand on the section about <topic x>". The task should be at most a few sentences.
        Do not provide it any additional context outside of the task parameter. It will automatically be fetched as needed by this tool.

        Args:
            path: The absolute or relative path to the file.
            task: The specific task to be performed on the document.
        """
        file_content = await read_file(ctx, path)

        # Determine the file type based on file extension
        file_path = Path(path)
        file_extension = file_path.suffix.lower()
        supported_extensions: dict[str, Literal["markdown", "latex"]] = {
            ".md": "markdown",
            ".tex": "latex",
        }

        if file_extension not in supported_extensions:
            return f"File type '{file_extension}' is not supported for editing. Currently supported types: {', '.join(supported_extensions.keys())}"

        file_type = supported_extensions[file_extension]

        editor = CommonEdit()
        request = EditRequest(
            context=ctx,
            request_type="mcp",
            file_content=file_content,
            task=task,
            file_type=file_type,
        )
        output = await editor.run(request)
        tool_output: str = output.change_summary + "\n" + output.output_message

        await write_file(ctx, path, output.new_content)
        return tool_output

    @mcp.tool()
    async def list_directory(ctx: Context, path: str) -> list[str]:
        """
        Lists all files and subdirectories in a directory.

        Args:
            path: The directory path to list.

        Returns:
            A list of filenames and subdirectory names. Files are prefixed with [FILE] and directories with [DIR].
        """
        dir_path = await validate_path(ctx, path)
        if not dir_path.exists() or not dir_path.is_dir():
            raise FileNotFoundError(f"Directory does not exist at {path}")

        try:
            return [("[DIR] " if entry.is_dir() else "[FILE] ") + entry.name for entry in dir_path.iterdir()]
        except Exception as e:
            raise RuntimeError(f"Failed to list directory contents at {path}: {str(e)}")

    return mcp
