# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from rich.columns import Columns
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from mcp_server.evals.common import load_test_cases
from mcp_server.llm.openai_chat_completion import openai_client
from mcp_server.markdown_edit.markdown_edit import run_markdown_edit
from mcp_server.types import (
    CustomContext,
    MarkdownEditOutput,
    MarkdownEditRequest,
)

logger = logging.getLogger(__name__)

load_dotenv(override=True)

WORD_TEST_CASES_PATH = Path(__file__).parents[2] / "data" / "word" / "test_cases.yaml"
WORD_TRANSCRIPT_PATH = Path(__file__).parents[2] / "data" / "word" / "transcripts"
ATTACHMENTS_DIR = Path(__file__).parents[2] / "data" / "attachments"


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
    custom_contexts = load_test_cases(test_case_type="writing")
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
