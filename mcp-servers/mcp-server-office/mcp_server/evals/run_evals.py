import asyncio
import logging
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from rich.columns import Columns
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from mcp_server.llm.openai_chat_completion import openai_client
from mcp_server.markdown_edit.markdown_edit import run_markdown_edit
from mcp_server.types import (
    AssistantMessage,
    CustomContext,
    MarkdownEditOutput,
    MarkdownEditRequest,
    MessageT,
    TestCase,
    UserMessage,
)

logger = logging.getLogger(__name__)

load_dotenv(override=True)

WORD_TEST_CASES_PATH = Path(__file__).parents[2] / "data" / "word" / "test_cases.yaml"
WORD_TRANSCRIPT_PATH = Path(__file__).parents[2] / "data" / "word" / "transcripts"
ATTACHMENTS_DIR = Path(__file__).parents[2] / "data" / "attachments"


def load_test_cases() -> list[CustomContext]:
    with Path.open(WORD_TEST_CASES_PATH, "r", encoding="utf-8") as f:
        test_cases = yaml.safe_load(f)["test_cases"]

    test_cases = [TestCase(**test_case) for test_case in test_cases]

    custom_contexts = []
    for test_case in test_cases:
        transcript_path = WORD_TRANSCRIPT_PATH / test_case.transcription_file

        # Load the transcript content
        with Path.open(transcript_path, "r", encoding="utf-8") as f:
            transcript_content = f.read()

        chat_history = _parse_transcript_to_chat_history(transcript_content)
        chat_history.append(UserMessage(content=test_case.next_ask))

        # Load and format attachments if they exist
        additional_context = ""
        if test_case.attachments:
            additional_context = _load_attachments(test_case.attachments)

        custom_contexts.append(
            CustomContext(
                chat_history=chat_history,
                document=test_case.document_markdown,
                additional_context=additional_context,
            )
        )

    return custom_contexts


def _parse_transcript_to_chat_history(transcript_content: str) -> list[MessageT]:
    """
    Parses the markdown transcript into a list of UserMessage and AssistantMessage objects.
    """

    # Split the transcript by message sections (marked by heading + divider)
    sections = transcript_content.split("----------------------------------")

    chat_history = []
    for section in sections:
        section = section.strip()
        if not section:
            continue

        if section.startswith("###"):
            lines = section.split("\n")
            header = lines[0]

            # Skip if there is no content or if it's a notice
            if len(lines) <= 1 or "notice:" in lines[2]:
                continue

            content = "\n".join(lines[1:]).strip()
            if not content:
                continue

            # Determine if this is an assistant message based on header
            if "Assistant" in header:
                chat_history.append(AssistantMessage(content=content))
            else:
                chat_history.append(UserMessage(content=content))

    return chat_history


def _load_attachments(attachment_filenames: list[str]) -> str:
    """
    Load attachment files and format them into the required XML-like format.

    Args:
        attachment_filenames: List of attachment filenames to load

    Returns:
        A string containing all formatted attachments
    """
    formatted_attachments = []

    for filename in attachment_filenames:
        file_path = ATTACHMENTS_DIR / filename

        if not file_path.exists():
            logger.warning(f"Attachment file {filename} not found at {file_path}")
            continue

        with Path.open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        formatted_attachment = f"<ATTACHMENT><FILENAME>{filename}</FILENAME><CONTENT>{content}</CONTENT></ATTACHMENT>"
        formatted_attachments.append(formatted_attachment)

    return "\n".join(formatted_attachments)


def print_markdown_edit_output(
    console: Console,
    output: MarkdownEditOutput,
    test_index: int,
    custom_context: CustomContext,
) -> None:
    """
    Print the markdown edit output to console using Rich formatting.
    """
    console.rule(f"Test Case {test_index} Results. Latency: {output.llm_latency:.2f} seconds.", style="cyan")

    console.print(
        Panel(
            custom_context.chat_history[-1].content,  # type: ignore
            title="User Request",
            border_style="blue",
            width=120,
        )
    )

    original_doc = Panel(
        Markdown(custom_context.document),
        title="Original Document",
        border_style="yellow",
        width=90,
    )
    new_doc = Panel(
        Markdown(output.new_markdown),
        title="Edited Document",
        border_style="green",
        width=90,
    )
    console.print(Columns([original_doc, new_doc]))

    console.print(
        Panel(
            output.change_summary or output.output_message,
            title="Change Summary",
            border_style="blue",
            width=120,
        )
    )

    console.print()


async def main() -> None:
    console = Console()
    custom_contexts = load_test_cases()
    client = openai_client(
        api_type="azure_openai",
        azure_endpoint=os.getenv("ASSISTANT__AZURE_OPENAI_ENDPOINT"),
        aoai_api_version="2025-01-01-preview",
    )

    for i, custom_context in enumerate(custom_contexts):
        markdown_edit_request = MarkdownEditRequest(
            context=custom_context,
            request_type="dev",
            chat_completion_client=client,
        )
        output = await run_markdown_edit(markdown_edit_request)
        print_markdown_edit_output(console, output, i + 1, custom_context)


if __name__ == "__main__":
    asyncio.run(main())
