# Copyright (c) Microsoft. All rights reserved.

from mcp.server.fastmcp import Context, FastMCP

from mcp_server import settings
from mcp_server.app_interaction.excel_editor import get_active_workbook, get_excel_app, get_workbook_content
from mcp_server.app_interaction.powerpoint_editor import (
    add_text_to_slide,
    get_active_presentation,
    get_powerpoint_app,
    get_presentation_content,
)
from mcp_server.app_interaction.word_editor import (
    get_active_document,
    get_markdown_representation,
    get_word_app,
)
from mcp_server.markdown_edit.comment_analysis import run_comment_analysis
from mcp_server.markdown_edit.feedback_step import run_feedback_step
from mcp_server.markdown_edit.markdown_edit import run_markdown_edit
from mcp_server.types import MarkdownEditRequest

server_name = "Office MCP Server"


def create_mcp_server() -> FastMCP:
    mcp = FastMCP(name=server_name, log_level=settings.log_level, host="127.0.0.1")

    @mcp.tool()
    async def edit_word_document(task: str, ctx: Context) -> str:
        """
        The user has a Microsoft Word document open side by side with this chat. Use this tool when you need to make changes to the document.
        You should provide it a task that you want it to do in the document. For example, if you want to have it expand on one section,
        you can say "expand on the section about <topic x>". The task should be a most a few sentences.
        Do not provide it any additional context outside of the task parameter. It will automatically be fetched as needed by this tool.
        """
        markdown_edit_output = await run_markdown_edit(
            markdown_edit_request=MarkdownEditRequest(context=ctx, task=task)
        )
        output_string = markdown_edit_output.change_summary + "\n" + markdown_edit_output.output_message
        return output_string

    @mcp.tool()
    async def add_comments_to_word_document(ctx: Context) -> str:
        """
        Runs a routine that will add feedback as comments to the currently open Word Document.
        """
        comment_output = await run_feedback_step(
            markdown_edit_request=MarkdownEditRequest(context=ctx),
        )
        return comment_output.feedback_summary

    @mcp.tool()
    async def analyze_comments(ctx: Context) -> str:
        """
        Runs a routine that analyze the comments in the Word document and determine how they could be solved.
        """
        comment_analysis_output = await run_comment_analysis(
            markdown_edit_request=MarkdownEditRequest(context=ctx),
        )
        return comment_analysis_output.edit_instructions + "\n" + comment_analysis_output.assistant_hints

    # TODO: It might be good to consider having the document content always be available to the assistant if the document is "connected".
    @mcp.tool()
    async def get_word_content(ctx: Context) -> str:
        """
        Returns the content of the open Word document. Use this tool when you just need the content of the document.
        If you need to make changes to the document, use the edit_word_document tool instead. It will automatically also get the current content of the document.
        """
        word = get_word_app()
        doc = get_active_document(word)
        markdown_from_word = get_markdown_representation(doc)
        return markdown_from_word

    @mcp.tool()
    async def get_powerpoint_content() -> str:
        """
        Returns the content of all slides in the active PowerPoint presentation.
        """
        powerpoint = get_powerpoint_app()
        presentation = get_active_presentation(powerpoint)
        return get_presentation_content(presentation)

    @mcp.tool()
    async def add_powerpoint_slide(slide_number: int, text: str) -> bool:
        """
        Adds a new slide at the specified position with the given text. Always call get_powerpoint_content to get the latest content and slide numbers.
        DO NOT use Markdown formatting for the text, it will not be rendered correctly. Use plaintext.
        At a maximum, add two bullet points to each slide.

        Args:
            slide_number: The position where to add the new slide
            text: The text to add to the slide

        Returns:
            True if the slide was added successfully, False otherwise
        """
        powerpoint = get_powerpoint_app()
        presentation = get_active_presentation(powerpoint)

        # Add new blank slide
        presentation.Slides.Add(slide_number, 12)

        # Add the text to the new slide
        add_text_to_slide(presentation, slide_number, text)
        return True

    @mcp.tool()
    async def remove_powerpoint_slide(slide_number: int) -> bool:
        """
        Removes the slide at the specified position. Always call get_powerpoint_content to get the latest content and slide numbers.

        Args:
            slide_number: The position of the slide to remove

        Returns:
            True if the slide was removed successfully, False otherwise
        """
        try:
            powerpoint = get_powerpoint_app()
            presentation = get_active_presentation(powerpoint)

            if slide_number <= 0 or slide_number > presentation.Slides.Count:
                return False

            presentation.Slides(slide_number).Delete()
            return True
        except Exception:
            return False

    @mcp.tool()
    async def get_excel_content() -> str:
        """
        Returns the content of the first worksheet in the active Excel workbook as a markdown table.

        Returns:
            A string containing the worksheet data formatted as a markdown table.
            First row is treated as headers.
        """
        excel = get_excel_app()
        workbook = get_active_workbook(excel)
        return get_workbook_content(workbook)

    return mcp
