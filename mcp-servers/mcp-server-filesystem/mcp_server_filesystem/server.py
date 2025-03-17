import logging
import sys
from pathlib import Path

from mcp.server.fastmcp import Context, FastMCP

from . import settings

# Set the name of the MCP server
server_name = "filesystem MCP Server"

# Set up logging
logger = logging.getLogger("mcp_server_filesystem")


# Helper function to get allowed directories from settings
async def get_allowed_directories(ctx: Context) -> list[Path]:
    # Return directories from settings
    if settings.allowed_directories:
        return [Path(directory).resolve() for directory in settings.allowed_directories]

    list_roots_result = await ctx.session.list_roots()
    if list_roots_result.roots:
        if sys.platform.startswith("win"):
            return [Path(root.uri.path.lstrip("/")).resolve() for root in list_roots_result.roots if root.uri.path]

        return [Path(root.uri.path).resolve() for root in list_roots_result.roots if root.uri.path]

    raise ValueError("No allowed_directories have been configured and no roots have been set.")


# Helper function to validate paths against allowed directories
async def validate_path(ctx: Context, requested_path: str) -> Path:
    # Get the current list of allowed directories
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


async def list_allowed_directories(ctx: Context) -> str:
    """
    Returns a string of allowed directories.

    Returns:
        A newline-separated string of allowed directories.
    """
    allowed_dirs = await get_allowed_directories(ctx)
    if not allowed_dirs:
        return "No allowed directories have been configured"
    return "\n".join(map(str, allowed_dirs))


# Define MCP tools as module-level functions
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


async def create_directory(ctx: Context, path: str) -> str:
    """
    Ensures that the specified directory exists, creating it if necessary.

    Args:
        path: The path to the directory to create.

    Returns:
        A confirmation message.
    """
    dir_path = await validate_path(ctx, path)

    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        return f"Directory at {path} successfully created."
    except Exception as e:
        raise RuntimeError(f"Failed to create directory {path}: {str(e)}")


async def edit_file(ctx: Context, path: str, edits: list[dict]) -> str:
    """
    Edits a file by replacing specified text sections with new content.

    Args:
        path: The file to edit.
        edits: A list of dictionaries with 'oldText' and 'newText'.

    Returns:
        A string representation of the changes (e.g., diff).
    """
    file = await validate_path(ctx, path)
    if not file.exists() or not file.is_file():
        raise FileNotFoundError(f"File does not exist at {path}")

    try:
        original_content = file.read_text(encoding="utf-8")
        modified_content = original_content

        for edit in edits:
            old_text = edit.get("oldText", "")
            new_text = edit.get("newText", "")

            if not old_text or not new_text:
                raise ValueError("Invalid edit specification. Must contain 'oldText' and 'newText'.")

            modified_content = modified_content.replace(old_text, new_text)

        file.write_text(modified_content, encoding="utf-8")
        return f"File at {path} successfully edited."
    except Exception as e:
        raise RuntimeError(f"Failed to edit the file at {path}: {str(e)}")


async def search_files(
    ctx: Context,
    root_path: str,
    pattern: str,
) -> list[str]:
    """
    Searches files and directories matching a pattern within a root path.

    Args:
        root_path: The directory to start searching from.
        pattern: The glob search pattern (e.g. '*.txt').

    Returns:
        A list of matching file paths.
    """
    root = await validate_path(ctx, root_path)

    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Root path does not exist at {root_path}")

    try:
        return [("[DIR] " if path.is_dir() else "[FILE] ") + str(path) for path in root.rglob(pattern)]
    except Exception as e:
        raise RuntimeError(f"Search failed in {root_path} using pattern {pattern}: {str(e)}")


async def get_file_info(ctx: Context, path: str) -> dict:
    """
    Retrieves metadata about a file or directory.

    Args:
        path: The path to the file or directory.

    Returns:
        A dictionary with file information (size, permissions, timestamps, etc.).
    """
    file = await validate_path(ctx, path)

    if not file.exists():
        raise FileNotFoundError(f"Path does not exist at {path}")

    try:
        stats = file.stat()
        return {
            "size": stats.st_size,
            "created": stats.st_ctime,
            "modified": stats.st_mtime,
            "accessed": stats.st_atime,
            "is_directory": file.is_dir(),
            "is_file": file.is_file(),
            "permissions": oct(stats.st_mode)[-3:],
        }
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve file info for {path}: {str(e)}")


async def read_multiple_files(ctx: Context, paths: list[str]) -> dict:
    """
    Reads the contents of multiple files. Returns a dictionary mapping file paths to their contents or error
    messages for files that cannot be accessed.

    Args:
        paths: A list of file paths to read.

    Returns:
        A dictionary where keys are file paths and values are their contents or error messages.
    """
    results = {}
    for path in paths:
        file = await validate_path(ctx, path)
        if not file.is_file():
            raise PermissionError(f"Path is not a file: {path}")
        try:
            results[path] = file.read_text(encoding="utf-8")
        except Exception as e:
            results[path] = f"Error: {str(e)}"
    return results


async def move_file(ctx: Context, source: str, destination: str) -> str:
    """
    Moves or renames a file or directory. Both source and destination paths must be valid and within allowed
    directories.

    Args:
        source: The path to the source file or directory.
        destination: The target path for the file or directory.

    Returns:
        A confirmation message confirming the move or rename operation.
    """
    src = await validate_path(ctx, source)
    dest = await validate_path(ctx, destination)
    try:
        src.rename(dest)
        return f"Successfully moved {source} to {destination}"
    except Exception as e:
        raise RuntimeError(f"Failed to move {source} to {destination}: {str(e)}")


def create_mcp_server() -> FastMCP:
    # Initialize FastMCP with debug logging
    mcp = FastMCP(name=server_name, log_level=settings.log_level)

    # Register tools with MCP
    mcp.tool()(read_file)
    mcp.tool()(write_file)
    mcp.tool()(list_directory)
    mcp.tool()(create_directory)
    mcp.tool()(edit_file)
    mcp.tool()(search_files)
    mcp.tool()(get_file_info)
    mcp.tool()(read_multiple_files)
    mcp.tool()(move_file)
    mcp.tool()(list_allowed_directories)

    return mcp
