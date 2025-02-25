from mcp.server.fastmcp import FastMCP
from . import settings
from pathlib import Path
import os

# Set the name of the MCP server
server_name = "filesystem MCP Server"

# Define MCP tools as module-level functions
def read_file(path: str) -> str:
    """
    Reads the content of a file specified by the path.

    Args:
        path: The absolute or relative path to the file.

    Returns:
        The content of the file as a string.
    """
    file = Path(path).resolve()

    if not file.exists() or not file.is_file():
        raise FileNotFoundError(f"File does not exist at path: {path}")

    try:
        return file.read_text(encoding="utf-8")
    except Exception as e:
        raise RuntimeError(f"Failed to read the file at {path}: {str(e)}")

def write_file(path: str, content: str) -> str:
    """
    Writes content to a file specified by the path. Creates the file if it does not exist.

    Args:
        path: The absolute or relative path to the file.
        content: The string content to write into the file.

    Returns:
        A confirmation message.
    """
    file = Path(path).resolve()
    try:
        file.parent.mkdir(parents=True, exist_ok=True)  # Ensure parent directories exist
        file.write_text(content, encoding="utf-8")
        return f"Successfully wrote content to {path}"
    except Exception as e:
        raise RuntimeError(f"Failed to write to the file at {path}: {str(e)}")

def list_directory(path: str) -> list[str]:
    """
    Lists all files and subdirectories in a directory.

    Args:
        path: The directory path to list.

    Returns:
        A list of filenames and subdirectory names.
    """
    dir_path = Path(path).resolve()
    if not dir_path.exists() or not dir_path.is_dir():
        raise FileNotFoundError(f"Directory does not exist at {path}")

    try:
        return [entry.name for entry in dir_path.iterdir()]
    except Exception as e:
        raise RuntimeError(f"Failed to list directory contents at {path}: {str(e)}")

def create_directory(path: str) -> str:
    """
    Ensures that the specified directory exists, creating it if necessary.

    Args:
        path: The path to the directory to create.

    Returns:
        A confirmation message.
    """
    dir_path = Path(path).resolve()

    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        return f"Directory at {path} successfully created."
    except Exception as e:
        raise RuntimeError(f"Failed to create directory {path}: {str(e)}")

def edit_file(path: str, edits: list[dict], dry_run: bool = False) -> str:
    """
    Edits a file by replacing specified text sections with new content.

    Args:
        path: The file to edit.
        edits: A list of dictionaries with 'oldText' and 'newText'.
        dry_run: If True, simulates the changes without writing.

    Returns:
        A string representation of the changes (e.g., diff).
    """
    file = Path(path).resolve()
    if not file.exists() or not file.is_file():
        raise FileNotFoundError(f"File does not exist at {path}")

    try:
        original_content = file.read_text(encoding="utf-8")
        modified_content = original_content

        for edit in edits:
            old_text = edit.get('oldText', '')
            new_text = edit.get('newText', '')

            if not old_text or not new_text:
                raise ValueError("Invalid edit specification. Must contain 'oldText' and 'newText'.")

            modified_content = modified_content.replace(old_text, new_text)

        if dry_run:
            return f"Dry run changes previewed successfully."

        file.write_text(modified_content, encoding="utf-8")
        return f"File at {path} successfully edited."
    except Exception as e:
        raise RuntimeError(f"Failed to edit the file at {path}: {str(e)}")

def search_files(root_path: str, pattern: str) -> list[str]:
    """
    Searches files and directories matching a pattern within a root path.

    Args:
        root_path: The directory to start searching from.
        pattern: The search pattern (e.g., '*.txt').

    Returns:
        A list of matching file paths.
    """
    root = Path(root_path).resolve()

    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Root path does not exist at {root_path}")

    try:
        return [str(file) for file in root.rglob(pattern)]
    except Exception as e:
        raise RuntimeError(f"Search failed in {root_path} using pattern {pattern}: {str(e)}")

def get_file_info(path: str) -> dict:
    """
    Retrieves metadata about a file or directory.

    Args:
        path: The path to the file or directory.

    Returns:
        A dictionary with file information (size, permissions, timestamps, etc.).
    """
    file = Path(path).resolve()

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

def create_mcp_server() -> FastMCP:
    # Initialize FastMCP with debug logging.
    mcp = FastMCP(name=server_name, log_level=settings.log_level)

    # Register tools with MCP
    mcp.tool()(read_file)
    mcp.tool()(write_file)
    mcp.tool()(list_directory)
    mcp.tool()(create_directory)
    mcp.tool()(edit_file)
    mcp.tool()(search_files)
    mcp.tool()(get_file_info)

    return mcp