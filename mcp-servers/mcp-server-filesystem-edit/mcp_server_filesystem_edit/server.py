# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from pathlib import Path
from textwrap import dedent
from urllib.parse import quote, unquote, urlparse

from mcp.server.fastmcp import Context, FastMCP
from mcp_extensions import list_client_resources, read_client_resource, write_client_resource
from mcp_extensions._server_extensions import ListResourcesResult, ReadResourceResult, TextResourceContents
from pydantic import AnyUrl

from mcp_server_filesystem_edit import settings
from mcp_server_filesystem_edit.app_handling.excel import get_worksheet_content_as_md_table
from mcp_server_filesystem_edit.app_handling.miktex import compile_tex_to_pdf
from mcp_server_filesystem_edit.app_handling.office_common import OfficeAppType, open_document_in_office
from mcp_server_filesystem_edit.app_handling.word import (
    get_markdown_representation,
    write_markdown,
)
from mcp_server_filesystem_edit.tools.add_comments import CommonComments
from mcp_server_filesystem_edit.tools.edit import CommonEdit
from mcp_server_filesystem_edit.types import FileOpRequest

# Set the name of the MCP server
server_name = "Filesystem Edit MCP Server"

logger = logging.getLogger("mcp_server_filesystem")


VIEW_BY_FILE_EXTENSIONS = [".md", ".tex", ".csv"]
VIEW_CUSTOM_EXTENSIONS = [".docx", ".xlsx", ".csv"]

EDIT_BY_FILE_EXTENSIONS = [".md", ".tex"]
EDIT_BY_APP_EXTENSIONS = [".docx"]


async def check_for_client_working_dir(ctx: Context) -> bool:
    """
    Returns True if the client has a root of "" set
    """
    list_roots_result = await ctx.session.list_roots()
    # Check if any of the roots match the client resource URI
    for root in list_roots_result.roots:
        if root.uri.host == "workspace":
            return True
    return False


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

        roots = [root for root in roots if root.is_dir() or (not root.exists() and not root.suffix)]
        if roots:
            first_root = roots[0]
            if not first_root.exists():
                logger.info(f"Creating directory from first root since it does not exist yet: {first_root}")
                first_root.mkdir(parents=True, exist_ok=True)
            return first_root

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
    is_client_resource = await check_for_client_working_dir(ctx)
    if is_client_resource:
        # Handle the path as a URI using urllib.parse
        try:
            uri = "file://workspace/" + requested_path
            uri = urlparse(requested_path)
            return Path(uri.path)
        except ValueError:
            raise ValueError(f"Invalid path: {requested_path}")

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


async def read_file(ctx: Context, path: Path) -> str:
    """
    Reads the content of a file specified by the path.

    Args:
        path: The absolute or relative path to the file.

    Returns:
        The content of the file as a string.
    """
    is_client_resource = await check_for_client_working_dir(ctx)
    if is_client_resource:
        try:
            uri = "client-resource:///" + quote(str(path))
            uri = AnyUrl(uri)
            read_result = await read_client_resource(ctx, uri)
            content = ""
            if isinstance(read_result, ReadResourceResult):
                for c in read_result.contents:
                    if isinstance(c, TextResourceContents):
                        content = c.text
            return content
        except Exception:
            return ""

    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"File does not exist at path: {path}")

    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        raise RuntimeError(f"Failed to read the file at {path}: {str(e)}")


async def write_file(ctx: Context, path: Path, content: str) -> None:
    """
    Writes the content to a file specified by the path.

    Args:
        path: The absolute or relative path to the file.
        content: The content to write to the file.
    """
    is_client_resource = await check_for_client_working_dir(ctx)
    if is_client_resource:
        try:
            uri = "client-resource:///" + quote(str(path))
            uri = AnyUrl(uri)
            write_result = await write_client_resource(ctx, uri, "text/plain", content.encode("utf-8"))
            logger.info(f"Write result: {write_result}")
        except Exception:
            return None
    else:
        try:
            path.write_text(content, encoding="utf-8")
        except Exception as e:
            raise RuntimeError(f"Failed to write to the file at {path}: {str(e)}")


def create_mcp_server() -> FastMCP:
    mcp = FastMCP(name=server_name, log_level=settings.log_level)

    @mcp.prompt(name="instructions", description="Instructions for the assistant regarding tool usage.")
    async def instructions_prompt(ctx: Context) -> str:
        return dedent("""
        ## Additional Tool Specific Guidance

        ### File Editing (Markdown) via `edit_file`

        - Assume that you should always be creating ".md" files, unless the user specifies otherwise.

        - Provide this tool specific instructions for what you want changed on this
        current step.

        - The editor may however make more changes than you expect. So after each
        step, be sure to check the document again. Based on the latest state of the
        document, come up with the next step.

        - This will also let you review the changes to make sure they would fully
        satisfy the user's ask.

        - Provide this tool specific instructions for what you want changed on this
        current step.

        - Do not try to use this to address comments that are not actionable.

        ### Feedback via `add_comments`

        - If you are working on writing documents for the user, call this tool to
        get another perspective on the document.

        - Whenever you think you are done, always then use this  tool get some more
        suggestions on how to improve.

        - If the user explicitly asks you to address comments call `add_comments`
        with `only_analyze=True` to first get suggestions on how to address the
        comments before editing.

        - If the feedback tool returns with comments that are not actionable,  DO
        NOT try to call the edit_file tool to address them. Instead either call
        other tools to try to get what is needed to address the comments, or ask the
        user.
        """).strip()

    @mcp.tool()
    async def list_working_directory(ctx: Context) -> str:
        """
        Lists all files in the working directory, including those in subdirs.
        Hidden directories (starting with '.') are excluded by default.

        Returns:
            Recursively returns all files in the working directory as relative paths.
        """

        # First check if we should take the assistant managed working directory path
        is_client_resource = await check_for_client_working_dir(ctx)
        if is_client_resource:
            client_resources = await list_client_resources(ctx)
            # Parse resources into a string that will let the model reference them correctly.
            if isinstance(client_resources, ListResourcesResult):
                file_string = ""
                for resource in client_resources.resources:
                    file_path = unquote(str(resource.uri).replace(resource.uri.scheme + "://", ""))
                    file_string += f"{file_path}\n"  # TODO:
            else:
                return f"Some error occurred while listing client resources:\n{client_resources}"
        else:
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
        validated_path = await validate_path(ctx, path)

        empty_file_string = f"{settings.file_tool_prefix}File viewed successfully, but it is currently empty."
        error_string = f"{settings.file_tool_prefix}File type not supported for filesystem reads: {validated_path}\nOnly {', '.join(VIEW_BY_FILE_EXTENSIONS + VIEW_CUSTOM_EXTENSIONS)} files are supported."

        file_extension = validated_path.suffix.lower()
        # Handle file types where we read them directly
        if file_extension in VIEW_BY_FILE_EXTENSIONS:
            file_content = await read_file(ctx, validated_path)
            if not file_content:
                return empty_file_string
            return file_content
        # Handle file types that need special code paths.
        elif file_extension in VIEW_CUSTOM_EXTENSIONS and settings.office_support_enabled:
            match file_extension:
                case ".docx":
                    _, document = open_document_in_office(validated_path, OfficeAppType.WORD)
                    file_content = get_markdown_representation(document)
                case ".xlsx":
                    _, document = open_document_in_office(validated_path, OfficeAppType.EXCEL)
                    file_content = get_worksheet_content_as_md_table(document)
                case _:
                    file_content = error_string
            return file_content
        else:
            return error_string

    @mcp.tool()
    async def edit_file(ctx: Context, path: str, task: str) -> str:
        """
        The user has a file editor corresponding to the file type, open like VSCode, Word, PowerPoint, TeXworks (+ MiKTeX), open side by side with this chat.
        Use this tool to create new files or edit existing ones.
        If you provide a new file path, it will be created for you and then the editor will start to edit it (from scratch).
        Name the file with capital letters and spacing like "Weekly AI Report.md" or "Email to Boss.md" since it will be directly shown to the user in that way.
        Provide a task that you want it to do in the document. For example, if you want to have it expand on one section,
        you can say "expand on the section about <topic x>". The task should be at most a few sentences.
        Do not provide it any additional context outside of the task parameter. It will automatically be fetched as needed by this tool.

        Args:
            path: The relative path to the file.
            task: The specific task that you want the document editor to do.
        """
        is_client_resource = await check_for_client_working_dir(ctx)
        validated_path = await validate_path(ctx, path)

        if not validated_path.exists() and not is_client_resource:
            try:
                validated_path.parent.mkdir(parents=True, exist_ok=True)
                validated_path.touch()
            except Exception as e:
                raise RuntimeError(f"Failed to create the file at {path}: {str(e)}")

        file_extension = validated_path.suffix.lower()
        if file_extension in EDIT_BY_FILE_EXTENSIONS:
            file_content = await read_file(ctx, validated_path)
            match file_extension:
                case ".md":
                    file_type = "markdown"
                case ".tex":
                    file_type = "latex"
                case _:
                    file_type = "markdown"
            request = FileOpRequest(
                context=ctx,
                request_type="mcp",
                file_content=file_content,
                task=task,
                file_type=file_type,
            )
            editor = CommonEdit()
            output = await editor.run(request)
            tool_output: str = output.change_summary + "\n" + output.output_message
            await write_file(ctx, validated_path, output.new_content)
            # If this is a tex file, auto compile it to PDF
            if file_type == "latex" and settings.pdflatex_enabled:
                success, error_msg = compile_tex_to_pdf(validated_path)
                if not success:
                    tool_output = f"\n\nError compiling LaTeX to PDF: {error_msg}\nPlease understand what caused the error and fix it in the LaTeX file in the next step."
                else:
                    tool_output += "\n\nLaTeX compiled successfully to PDF."
        elif file_extension in EDIT_BY_APP_EXTENSIONS and settings.office_support_enabled:
            # Word (.docx) is currently the only supported app for editing
            _, document = open_document_in_office(validated_path, OfficeAppType.WORD)
            file_content = get_markdown_representation(document)
            request = FileOpRequest(
                context=ctx,
                request_type="mcp",
                file_content=file_content,
                task=task,
                file_type="word",
            )
            editor = CommonEdit()
            output = await editor.run(request)
            tool_output: str = output.change_summary + "\n" + output.output_message
            write_markdown(document, output.new_content)
        else:
            tool_output = f"{settings.file_tool_prefix}File type not supported for editing: {validated_path}\nOnly {', '.join(EDIT_BY_FILE_EXTENSIONS + EDIT_BY_APP_EXTENSIONS)} files are supported."
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
        is_client_resource = await check_for_client_working_dir(ctx)
        validated_path = await validate_path(ctx, path)
        # Error if the file does not exist
        if not validated_path.exists() and not is_client_resource:
            return "File does not exist at path: `{path}`"

        file_extension = validated_path.suffix.lower()
        if file_extension in EDIT_BY_FILE_EXTENSIONS:
            file_content = await read_file(ctx, validated_path)
            if not file_content:
                return f"{settings.file_tool_prefix}This file is empty so I am not adding any comments."
            match file_extension:
                case ".md":
                    file_type = "markdown"
                case ".tex":
                    file_type = "latex"
                case _:
                    file_type = "markdown"
            commenter = CommonComments()
            request = FileOpRequest(
                context=ctx,
                request_type="mcp",
                file_content=file_content,
                file_type=file_type,
            )
            output = await commenter.run(request, only_analyze=only_analyze)
            await write_file(ctx, validated_path, output.new_content)
            tool_output = output.comment_instructions
        elif file_extension in EDIT_BY_APP_EXTENSIONS and settings.office_support_enabled:
            # Word (.docx) is currently the only supported app for commenting
            _, document = open_document_in_office(validated_path, OfficeAppType.WORD)
            file_content = get_markdown_representation(document)
            request = FileOpRequest(
                context=ctx,
                request_type="mcp",
                file_content=file_content,
                file_type="word",
            )
            commenter = CommonComments()
            output = await commenter.run(request, only_analyze=only_analyze)
            if not only_analyze:  # Don't need to rewrite if only analysis was done.
                write_markdown(document, output.new_content)
            tool_output = output.comment_instructions
        else:
            tool_output = f"{settings.file_tool_prefix}File type not supported for commenting: {validated_path}\nOnly {', '.join(EDIT_BY_FILE_EXTENSIONS + EDIT_BY_APP_EXTENSIONS)} files are supported."
        return tool_output

    @mcp.resource(
        uri="resource://filesystem_edit/open_files",
        name="Open Files",
        description="The file(s) the user is currently working on with the assistant and should be placed in its context",
        mime_type="text/plain",
    )
    async def file_context() -> str:
        """
        # TODO: BROKEN DONT USE
        Looks at the context files, and formats then into a string for the assistant to place in its context window.
        # TODO: Eventually this should take a similar path as the view tool to read files.
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
