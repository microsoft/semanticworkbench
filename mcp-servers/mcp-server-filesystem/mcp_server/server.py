import logging
import sys
from pathlib import Path
import os
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from . import settings

# Set the name of the MCP server
server_name = "filesystem MCP Server"

# Set up logging
logger = logging.getLogger("mcp_server_filesystem")

# Helper function to get allowed directories from settings
def get_allowed_directories():
    # Return directories from settings
    if settings.allowed_directories:
        return [Path(directory).resolve() for directory in settings.allowed_directories]
    # Return empty list if none found
    return []

# Helper function to validate paths against allowed directories
def validate_path(requested_path: str) -> Path:
    # Get the current list of allowed directories
    allowed_dirs = get_allowed_directories()

    if not allowed_dirs:
        raise PermissionError("No allowed_directories have been configured")

    absolute_path = Path(requested_path).resolve()
    for allowed_dir in allowed_dirs:
        if str(absolute_path).startswith(str(allowed_dir)):
            return absolute_path
    raise PermissionError(f"Access denied: {requested_path} is outside allowed_directories: {allowed_dirs}")

# Define MCP tools as module-level functions
def read_file(path: str) -> str:
    """
    Reads the content of a file specified by the path.

    Args:
        path: The absolute or relative path to the file.

    Returns:
        The content of the file as a string.
    """
    file = validate_path(path)
    file = validate_path(path)

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
    file = validate_path(path)
    file = validate_path(path)
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
    dir_path = validate_path(path)
    dir_path = validate_path(path)
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
    dir_path = validate_path(path)
    dir_path = validate_path(path)

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
    file = validate_path(path)
    file = validate_path(path)
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
    root = validate_path(root_path)
    root = validate_path(root_path)

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
    file = validate_path(path)
    file = validate_path(path)

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

def read_multiple_files(paths: list[str]) -> dict:
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
        file = validate_path(path)
        if not file.is_file():
            raise PermissionError(f"Path is not a file: {path}")
        try:
            results[path] = file.read_text(encoding="utf-8")
        except Exception as e:
            results[path] = f"Error: {str(e)}"
    return results

def move_file(source: str, destination: str) -> str:
    """
    Moves or renames a file or directory. Both source and destination paths must be valid and within allowed
    directories.

    Args:
        source: The path to the source file or directory.
        destination: The target path for the file or directory.

    Returns:
        A confirmation message confirming the move or rename operation.
    """
    src = validate_path(source)
    dest = validate_path(destination)
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

    @mcp.tool()
    def list_allowed_directories() -> str:
        """
        Returns a string of allowed directories.

        Returns:
            A newline-separated string of allowed directories.
        """
        allowed_dirs = get_allowed_directories()
        if not allowed_dirs:
            return "No allowed directories have been configured"
        return '\n'.join(map(str, allowed_dirs))

    # Create a custom run_sse_async method to replace the standard one
    # This will allow us to intercept URL parameters
    original_run_sse_async = mcp.run_sse_async

    async def custom_run_sse_async():
        sse = SseServerTransport("/messages/")

        async def handle_sse(request: Request):
            # Log the connection details
            logger.info("Handling SSE connection request")

            # Parse and process query parameters
            query_params = dict(request.query_params)
            logger.info(f"Query parameters: {query_params}")

            # Look specifically for the 'args' parameter
            directories = []
            
            if 'args' in query_params:
                args_value = query_params['args']
                # Split the comma-separated list of directories
                if args_value and ',' in args_value:
                    directories = [d.strip() for d in args_value.split(',') if d.strip()]
                elif args_value.strip():
                    # Single directory
                    directories.append(args_value.strip())
                    
                logger.info(f"Found directories in 'args' parameter: {directories}")
            if directories:
                settings.allowed_directories = directories
                logger.info(f"Setting allowed_directories from query parameters: {directories}")
            else:
                logger.error("No directories provided in 'args' parameter")
                return PlainTextResponse(
                    "Error: No directories provided in 'args' parameter. Use /sse?args=/path1,/path2,/path3 format",
                    status_code=400
                )

            # Get the allowed directories from settings after our update
            allowed_dirs = get_allowed_directories()
            logger.info(f"Proceeding with allowed_directories: {allowed_dirs}")

            # Continue with normal SSE connection
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await mcp._mcp_server.run(
                    streams[0],
                    streams[1],
                    mcp._mcp_server.create_initialization_options(),
                )

        starlette_app = Starlette(
            debug=mcp.settings.debug,
            routes=[
                Route("/sse", endpoint=handle_sse),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        import uvicorn
        config = uvicorn.Config(
            starlette_app,
            host=mcp.settings.host,
            port=mcp.settings.port,
            log_level=mcp.settings.log_level.lower(),
        )
        server = uvicorn.Server(config)
        await server.serve()

    # Replace the run_sse_async method
    mcp.run_sse_async = custom_run_sse_async

    return mcp