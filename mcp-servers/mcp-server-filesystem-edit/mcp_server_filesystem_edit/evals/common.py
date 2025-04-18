# Copyright (c) Microsoft. All rights reserved.

import logging
from pathlib import Path
from typing import Literal

import yaml
from mcp_extensions.llm.llm_types import AssistantMessage, MessageT, UserMessage

from mcp_server_filesystem_edit.types import (
    CustomContext,
    TestCase,
)

WORD_TEST_CASES_PATH = Path(__file__).parents[2] / "data" / "test_cases.yaml"
WORD_TRANSCRIPT_PATH = Path(__file__).parents[2] / "data" / "transcripts"
ATTACHMENTS_DIR = Path(__file__).parents[2] / "data" / "attachments"

logger = logging.getLogger(__name__)


def load_test_cases(
    test_case_type: Literal["writing", "comments", "presentation"] | None = None,
) -> list[CustomContext]:
    """
    Load test cases and convert them to CustomContext objects.

    Args:
        test_case_type: Optional filter to only return test cases of a specific type.
        If None, returns all test cases.

    Returns:
        A list of CustomContext objects representing the test cases.
    """
    with Path.open(WORD_TEST_CASES_PATH, "r", encoding="utf-8") as f:
        test_cases = yaml.safe_load(f)["test_cases"]

    test_cases = [TestCase(**test_case) for test_case in test_cases]

    if test_case_type is not None:
        test_cases = [tc for tc in test_cases if tc.test_case_type == test_case_type]

    custom_contexts = []
    for test_case in test_cases:
        transcript_path = WORD_TRANSCRIPT_PATH / test_case.transcription_file
        with Path.open(transcript_path, "r", encoding="utf-8") as f:
            transcript_content = f.read()

        chat_history = _parse_transcript_to_chat_history(transcript_content)
        chat_history.append(UserMessage(content=test_case.next_ask))

        additional_context = ""
        if test_case.attachments:
            additional_context = _load_attachments(test_case.attachments)

        document_content = ""
        if test_case.open_file:
            document_path = ATTACHMENTS_DIR / test_case.open_file
            if document_path.exists():
                with Path.open(document_path, "r", encoding="utf-8") as f:
                    document_content = f.read()
            else:
                logger.warning(f"Document file {test_case.open_file} not found at {document_path}")

        custom_contexts.append(
            CustomContext(
                chat_history=chat_history,
                document=document_content,
                file_type=test_case.file_type,
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
