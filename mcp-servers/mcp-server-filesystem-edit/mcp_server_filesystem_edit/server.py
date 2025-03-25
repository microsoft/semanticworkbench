# Copyright (c) Microsoft. All rights reserved.

import sys
from pathlib import Path

from mcp.server.fastmcp import Context, FastMCP

from mcp_server_filesystem_edit import settings
from mcp_server_filesystem_edit.app_handling.miktex import compile_tex_to_pdf
from mcp_server_filesystem_edit.app_handling.word import (
    get_markdown_representation,
    open_document_in_word,
    write_markdown,
)
from mcp_server_filesystem_edit.tools.add_comments import CommonComments
from mcp_server_filesystem_edit.tools.edit import CommonEdit
from mcp_server_filesystem_edit.types import FileForChanges, FileOpRequest

# Set the name of the MCP server
server_name = "Filesystem Edit MCP Server"

# Assume these are mutually exclusive
SUPPORTED_APP_EXTENSIONS = [".docx"]
SUPPORTED_FILE_ONLY_EXTENSIONS = [".md", ".tex"]


async def get_allowed_directory(ctx: Context) -> Path:
    """
    Helper function to get allowed directory.
    If no allowed directory is configured through settings, it will use roots where
    it use the first root as the allowed or "working" directory.
    """
    if settings.allowed_directories:
        return Path(settings.allowed_directories[0]).resolve()

    list_roots_result = await ctx.session.list_roots()
    if list_roots_result.roots:
        if sys.platform.startswith("win"):
            roots = [Path(root.uri.path.lstrip("/")).resolve() for root in list_roots_result.roots if root.uri.path]
        else:
            roots = [Path(root.uri.path).resolve() for root in list_roots_result.roots if root.uri.path]

        roots = [root for root in roots if root.is_dir()]
        if roots:
            return roots[0]

    raise ValueError("No allowed_directories have been configured and no roots have been set.")


async def get_context_files(ctx: Context, allowed_file_extensions: list[str] = [".md", ".tex"]) -> list[Path]:
    """
    Parses roots for any paths that refer to files with the allowed extensions

    Returns:
        List of Path objects for files with allowed extensions
    """
    files = []
    if settings.allowed_directories:
        # If allowed directories are specified, look for files in those directories
        for directory in settings.allowed_directories:
            dir_path = Path(directory).resolve()
            if dir_path.exists() and dir_path.is_dir():
                # Add all files in this directory with allowed extensions (non-recursive)
                files.extend([
                    f for f in dir_path.iterdir() if f.is_file() and f.suffix.lower() in allowed_file_extensions
                ])
        return files

    # If no allowed directories, try to get files from roots
    list_roots_result = await ctx.session.list_roots()
    if list_roots_result.roots:
        for root in list_roots_result.roots:
            if not root.uri.path:
                continue
            root_path = (
                Path(root.uri.path.lstrip("/")).resolve()
                if sys.platform.startswith("win")
                else Path(root.uri.path).resolve()
            )
            # Check if this root points to a file with allowed extension
            if root_path.exists() and root_path.is_file() and root_path.suffix.lower() in allowed_file_extensions:
                files.append(root_path)
    return files


async def validate_path(ctx: Context, requested_path: str) -> Path:
    """
    Helper function to validate the provided paths against the allowed working directory and
    returns the absolute path.

    Args:
        requested_path: The path to validate.

    Returns:
        The absolute path of the file.
    """
    allowed_dir = await get_allowed_directory(ctx)
    requested_path_obj = Path(requested_path)

    # If the path is absolute, check if it's within the allowed directory
    if requested_path_obj.is_absolute():
        resolved_path = requested_path_obj.resolve()
        if not str(resolved_path).startswith(str(allowed_dir)):
            raise ValueError(f"Path {requested_path} is outside of allowed directory {allowed_dir}")
        return resolved_path
    else:
        # For relative paths, join with the allowed directory
        return (allowed_dir / requested_path_obj).resolve()


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


async def read_file_for_edits(ctx: Context, path: str) -> FileForChanges:
    validated_path = await validate_path(ctx, path)
    error_msg = None

    # Check if the file exists and if not, create it
    if not validated_path.exists():
        try:
            validated_path.parent.mkdir(parents=True, exist_ok=True)
            validated_path.touch()
        except Exception as e:
            raise RuntimeError(f"Failed to create the file at {path}: {str(e)}")

    # For file_only extensions, we read as normal.
    if any(path.endswith(ext) for ext in SUPPORTED_FILE_ONLY_EXTENSIONS):
        file_type = "markdown" if path.endswith(".md") else "latex"
        file_content = await read_file(ctx, path)

    # For extensions that we can handle in an app, go down the app specific path.
    elif any(path.endswith(ext) for ext in SUPPORTED_APP_EXTENSIONS):
        file_type = "word" if path.endswith(".docx") else "word"
        _, document = open_document_in_word(validated_path)
        file_content = get_markdown_representation(document)
    else:
        error_msg = f"File type not supported: {path}"
        file_type = "markdown"
        file_content = ""

    output = FileForChanges(
        file_path=validated_path, file_content=file_content, file_type=file_type, error_msg=error_msg
    )
    return output


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

    # For file_only extensions, read them as normal.
    if any(path.endswith(ext) for ext in SUPPORTED_FILE_ONLY_EXTENSIONS):
        try:
            file.parent.mkdir(parents=True, exist_ok=True)  # Ensure parent directories exist
            file.write_text(content, encoding="utf-8")
            return f"Successfully wrote content to {path}"
        except Exception as e:
            raise RuntimeError(f"Failed to write to the file at {path}: {str(e)}")
    elif any(path.endswith(ext) for ext in SUPPORTED_APP_EXTENSIONS):
        # For extensions that we can handle in an app, go down the app specific path.
        _, document = open_document_in_word(file)
        write_markdown(document, content)
        return f"Successfully wrote content to {path}"
    else:
        raise ValueError(f"File type not supported: {path}\nOnly .md, .tex, and .docx files are supported. ")


def create_mcp_server() -> FastMCP:
    mcp = FastMCP(name=server_name, log_level=settings.log_level)

    @mcp.tool()
    async def list_working_directory(ctx: Context) -> str:
        """
        Lists all files in the working directory, including those in subdirs.
        Hidden directories (starting with '.') are excluded by default.

        Returns:
            Recursively returns all files in the working directory as relative paths.
        """
        allowed_dir = await get_allowed_directory(ctx)
        all_files = [f for f in allowed_dir.glob("**/*") if f.is_file()]

        file_string = ""
        for file in all_files:
            # Skip files in hidden directories unless include_hidden_paths is enabled
            if not settings.include_hidden_paths and any(part.startswith(".") for part in file.parts):
                continue

            relative_path = file.relative_to(allowed_dir)
            file_string += f"{relative_path}\n"

        return (
            file_string.strip()
            if file_string
            else f"{settings.file_tool_prefix}No files found in the working directory."
        )

    @mcp.tool()
    async def view(ctx: Context, path: str) -> str:
        """
        Reads the content of a file specified by the path.

        Args:
            path: The relative path to the file.

        Returns:
            The content of the file as a string.
        """
        empty_file_string = f"{settings.file_tool_prefix}File viewed successfully, but it is currently empty."

        # If this is an app supported file, read it in the app using read_file_for_edits
        if any(path.endswith(ext) for ext in SUPPORTED_APP_EXTENSIONS):
            file_content = await read_file_for_edits(ctx, path)
            if file_content.error_msg:
                return file_content.error_msg
            elif not file_content.file_content:
                return empty_file_string
            else:
                return file_content.file_content
        else:
            file_content = await read_file(ctx, path)
            if not file_content:
                return empty_file_string
            return file_content

    @mcp.tool()
    async def edit_file(ctx: Context, path: str, task: str) -> str:
        """
        The user has a file editor corresponding to the file type, open like VSCode, Word, PowerPoint, TeXworks (+ MiKTeX), open side by side with this chat.
        Use this tool to create new files or edit existing ones.
        If you provide a new file path, it will be created for you and then the editor will start to edit it (from scratch).
        Provide a task that you want it to do in the document. For example, if you want to have it expand on one section,
        you can say "expand on the section about <topic x>". The task should be at most a few sentences.
        Do not provide it any additional context outside of the task parameter. It will automatically be fetched as needed by this tool.

        Args:
            path: The relative path to the file.
            task: The specific task that you want the document editor to do.
        """
        read_file_result = await read_file_for_edits(ctx, path)
        if read_file_result.error_msg:
            return read_file_result.error_msg

        editor = CommonEdit()
        request = FileOpRequest(
            context=ctx,
            request_type="mcp",
            file_content=read_file_result.file_content,
            task=task,
            file_type=read_file_result.file_type,
        )
        output = await editor.run(request)
        tool_output: str = output.change_summary + "\n" + output.output_message

        await write_file(ctx, path, output.new_content)

        # If this is a tex file, auto compile it to PDF
        if read_file_result.file_type == "latex" and settings.pdflatex_enabled:
            success, error_msg = compile_tex_to_pdf(read_file_result.file_path)
            if not success:
                tool_output = f"\n\nError compiling LaTeX to PDF: {error_msg}\nPlease understand what caused the error and fix it in the LaTeX file in the next step."
            else:
                tool_output += "\n\nLaTeX compiled successfully to PDF."

        return tool_output

    @mcp.tool()
    async def add_comments(ctx: Context, path: str, only_analyze: bool = False) -> str:
        """
        Adds feedback as comments to an existing file and to get suggestions on how to address them.
        Use this to help continually improve a document.
        If the user only wants to address the current comments, set only_analyze to True.
        This will not add any new comments and only figure how to address the current ones.

        Args:
            path: The relative path to the file.
            only_analyze: If True, only analyze the currently available comments without adding them.

        Returns:
            A summary of the comments added and suggestions for how to address them.
        """
        read_file_result = await read_file_for_edits(ctx, path)
        if read_file_result.error_msg:
            return read_file_result.error_msg

        commenter = CommonComments()
        request = FileOpRequest(
            context=ctx,
            request_type="mcp",
            file_content=read_file_result.file_content,
            file_type=read_file_result.file_type,
        )
        output = await commenter.run(request, only_analyze=only_analyze)
        await write_file(ctx, path, output.new_content)
        return output.comment_instructions

    @mcp.resource(
        uri="resource://filesystem_edit/open_files",
        name="Open Files",
        description="The file(s) the user is currently working on with the assistant and should be placed in its context",
        mime_type="text/plain",
    )
    async def file_context() -> str:
        """
        Looks at the context files, and formats then into a string for the assistant to place in its context window.
        """
        try:
            ctx = mcp.get_context()
            context_files = await get_context_files(ctx)  # type: ignore
            file_context_string = ""
            for file_path in context_files:
                file_content = await read_file(ctx, str(file_path))  # type: ignore
                if file_content:
                    file_context_string += f'<document path="{file_path}">{file_content}\n</document>\n'
            if file_context_string:
                file_context_string = (
                    "The user is working on the following files and this is their current content:\n"
                    + file_context_string
                )
            return file_context_string.strip()
        except Exception:
            return ""

    return mcp
