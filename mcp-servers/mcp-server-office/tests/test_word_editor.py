# Copyright (c) Microsoft. All rights reserved.

import time

import pytest
from mcp_server.app_interaction.word_editor import (
    WordCommentData,
    add_document_comment,
    delete_comments_containing_text,
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
    markdown_text = get_markdown_representation(word_document, include_comments=True)
    assert markdown_text is not None


def test_write_markdown_to_document_round_trip(word_document):
    """
    This will show what is lost when we convert to markdown and back to Word.
    """
    markdown_text = get_markdown_representation(word_document)
    write_markdown_to_document(word_document, markdown_text)


def test_read_write_document_content(word_document):
    markdown_text = """- hello!
# Introduction to Python
Python is a high-level, **interpreted** programming language *known* for its ***simplicity*** and readability. It is widely used for web development, data analysis, artificial intelligence, and more.

- ***Easy to Read and Write***: Python's syntax is clear and concise.
- **Cross-Platform**: Works on Windows, macOS, and Linux.

## Installing Python

To install Python, follow these steps:
1. Download the latest version for your operating system.
1. Run the installer and *follow* the instructions.
1. Verify the installation by running `python --version` in the terminal.

That's all!"""
    write_markdown_to_document(word_document, markdown_text)
    rt_markdown_text = get_markdown_representation(word_document)
    write_markdown_to_document(word_document, rt_markdown_text)


def test_write_markdown_to_document_lists(word_document):
    markdown_text = """## Market Opportunity
Here are the market opportunities:
- Growing Market: The market is projected to grow.
- Target Audience: Our primary customers are enterprises.
Let's get into the details."""
    write_markdown_to_document(word_document, markdown_text)


def test_read_markdown_list_ending(word_document):
    """
    Tests what happens when reading a new paragraph after a list.
    """
    markdown_text = """Pros:
1. Direct integration
2. Focus on accessibility and consistency.
**Cons**:
1. Potential overlap
2. Requires navigating and configuring docs
## A heading
- A new bullet
- Another bullet"""
    write_markdown_to_document(word_document, markdown_text)
    rt_markdown_text = get_markdown_representation(word_document)
    print(rt_markdown_text)


def test_read_markdown_code(word_document):
    markdown_text = """This example illustrates a very simple Python program.
```python
a = 2
b = 3
total = a + b
if total > 4:
    print(f"Hello, the answer is {a + b}")

```
This is a new paragraph after the code block.
"""
    write_markdown_to_document(word_document, markdown_text)
    rt_markdown_text = get_markdown_representation(word_document)
    print(rt_markdown_text)


def test_read_markdown_code_2(word_document):
    markdown_text = """- item 1
- item 2
- item 3
```python
a = 2
b = 3
total = a + b
if total > 4:
    print(f"Hello, the answer is {a + b}")

```
#### This is a heading 4
1. item 1
1. item 2
And here is a regular paragraph"""
    write_markdown_to_document(word_document, markdown_text)
    rt_markdown_text = get_markdown_representation(word_document)
    print(rt_markdown_text)


def test_comments(word_document):
    markdown_text = "This is some text in my document."
    write_markdown_to_document(word_document, markdown_text)
    text_to_remove = "This is a comment."
    comment_data = WordCommentData(
        comment_text=text_to_remove,
        location_text="some text",
    )
    add_document_comment(word_document, comment_data)
    time.sleep(2)
    delete_comments_containing_text(word_document, text_to_remove)
