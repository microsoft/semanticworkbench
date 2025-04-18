# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from mcp_extensions.llm.openai_chat_completion import openai_client
from rich.columns import Columns
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from mcp_server_filesystem_edit.app_handling.office_common import OfficeAppType, open_document_in_office
from mcp_server_filesystem_edit.app_handling.powerpoint import write_markdown
from mcp_server_filesystem_edit.evals.common import load_test_cases
from mcp_server_filesystem_edit.tools.edit import PowerpointEdit
from mcp_server_filesystem_edit.types import (
    CustomContext,
    EditOutput,
    FileOpRequest,
)

logger = logging.getLogger(__name__)

load_dotenv(override=True)


def print_edit_output(
    console: Console,
    output: EditOutput,
    test_index: int,
    custom_context: CustomContext,
) -> None:
    """
    Print the edit output to console using Rich formatting.
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
        Markdown(output.new_content),
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
    test_case_type = "presentation"
    custom_contexts = load_test_cases(test_case_type=test_case_type)
    client = openai_client(
        api_type="azure_openai",
        azure_endpoint=os.getenv("ASSISTANT__AZURE_OPENAI_ENDPOINT"),
        aoai_api_version="2025-01-01-preview",
    )

    for i, custom_context in enumerate(custom_contexts):
        edit_request = FileOpRequest(
            context=custom_context,
            file_type=custom_context.file_type,
            request_type="dev",
            chat_completion_client=client,
            file_content=custom_context.document,
        )
        editor = PowerpointEdit()

        output = await editor.run(edit_request)
        print_edit_output(console, output, i + 1, custom_context)

        output_path = Path(__file__).parents[2] / "temp" / "created_presentation.pptx"  # type: ignore
        _, document = open_document_in_office(output_path, OfficeAppType.POWERPOINT)
        write_markdown(
            document,
            output.new_content,
        )


if __name__ == "__main__":
    asyncio.run(main())
