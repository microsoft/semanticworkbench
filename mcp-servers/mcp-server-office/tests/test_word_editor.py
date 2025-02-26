# Copyright (c) Microsoft. All rights reserved.

import pytest
from mcp_server.app_interaction.word_editor import (
    get_active_document,
    get_markdown_representation,
    get_word_app,
    write_markdown_to_document,
)


@pytest.fixture
def word_document():
    """Fixture that provides an active Word document."""
    word_app = get_word_app()
    doc = get_active_document(word_app)
    yield doc
    # Optional cleanup if needed
    # You might want to close the document without saving changes
    # doc.Close(SaveChanges=False)
    # Or you might want to keep Word open for debugging


def test_get_markdown_representation_1(word_document):
    markdown_text = get_markdown_representation(word_document)
    assert markdown_text is not None


def test_write_markdown_to_document(word_document):
    markdown_text = get_markdown_representation(word_document)
    write_markdown_to_document(word_document, markdown_text)
