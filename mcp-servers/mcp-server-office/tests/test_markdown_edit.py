# Copyright (c) Microsoft. All rights reserved.

from mcp_server.app_interaction.word_editor import get_active_document, get_word_app, write_markdown_to_document
from mcp_server.markdown_edit.markdown_edit import run_markdown_edit


def test_run_markdown_edit():
    document_context = "# A Cliptastic Adventure"
    word_app = get_word_app()
    doc = get_active_document(word_app)
    write_markdown_to_document(doc, document_context)

    chat_history = "User: write me story about a modern day Clippy in one paragraph."
    additional_context = ""
    output_message = run_markdown_edit(chat_history, additional_context)
    assert output_message is not None
    assert output_message != ""


if __name__ == "__main__":
    test_run_markdown_edit()
