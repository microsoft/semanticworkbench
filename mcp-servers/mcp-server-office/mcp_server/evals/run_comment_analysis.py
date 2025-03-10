# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from rich.console import Console

from mcp_server.evals.common import load_test_cases
from mcp_server.llm.openai_chat_completion import openai_client
from mcp_server.markdown_edit.comment_analysis import run_comment_analysis
from mcp_server.types import (
    MarkdownEditRequest,
)


async def main() -> None:
    console = Console()
    custom_contexts = load_test_cases(test_case_type="comment_analysis")
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
        output = await run_comment_analysis(markdown_edit_request)
        console.print(output)


if __name__ == "__main__":
    asyncio.run(main())
