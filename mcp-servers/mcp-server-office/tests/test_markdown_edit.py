# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from dotenv import load_dotenv
from mcp_server.app_interaction.word_editor import get_active_document, get_word_app, write_markdown_to_document
from mcp_server.llm.openai_chat_completion import openai_client
from mcp_server.markdown_edit.markdown_edit import run_markdown_edit
from mcp_server.types import CustomContext, MarkdownEditRequest, UserMessage

load_dotenv(override=True)


async def test_run_markdown_edit():
    document_context = "# A Cliptastic Adventure"
    word_app = get_word_app()
    doc = get_active_document(word_app)
    write_markdown_to_document(doc, document_context)

    chat_history = "User: Write me story about a modern day Clippy in one paragraph."
    additional_context = ""
    context = CustomContext(
        chat_history=[UserMessage(content=chat_history)],
        document=document_context,
        additional_context=additional_context,
    )
    client = openai_client(
        api_type="azure_openai",
        azure_endpoint=os.getenv("ASSISTANT__AZURE_OPENAI_ENDPOINT"),
        aoai_api_version="2025-01-01-preview",
    )
    output_message = await run_markdown_edit(
        MarkdownEditRequest(context=context, request_type="dev", chat_completion_client=client)
    )
    assert output_message is not None
    assert output_message != ""


if __name__ == "__main__":
    asyncio.run(test_run_markdown_edit())
