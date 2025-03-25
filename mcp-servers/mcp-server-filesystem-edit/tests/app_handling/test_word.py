from pathlib import Path

import pytest
from mcp_server_filesystem_edit.app_handling.word import (
    get_markdown_representation,
    open_document_in_word,
    write_markdown,
)

TEMP_FILES_PATH = Path(__file__).parents[2] / "temp" / "tests"
TEMP_FILES_PATH.mkdir(exist_ok=True)
TEST_FILE = TEMP_FILES_PATH / "test_document.docx"


@pytest.fixture
def word_document():
    """Fixture that provides an active Word document."""
    _, doc = open_document_in_word(TEMP_FILES_PATH / "test_document.docx")
    # Make sure the document is empty before each test
    doc.Content.Delete()  # type: ignore
    yield doc


def test_markdown_roundtrip(word_document, markdown_text: str) -> str:
    """
    Helper function that performs a roundtrip test:
    1. Writes markdown to a Word document
    2. Reads it back as markdown
    3. Writes the read markdown back to the document

    Returns the markdown representation after the first write.
    """
    write_markdown(word_document, markdown_text)
    rt_markdown_text = get_markdown_representation(word_document)
    write_markdown(word_document, rt_markdown_text)
    return rt_markdown_text


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
    test_markdown_roundtrip(word_document, markdown_text)


def test_write_markdown_to_document_lists(word_document):
    markdown_text = """## Market Opportunity
Here are the market opportunities:
- Growing Market: The market is projected to grow.
- Target Audience: Our primary customers are enterprises.
Let's get into the details."""
    test_markdown_roundtrip(word_document, markdown_text)


def test_read_markdown_list_ending(word_document):
    markdown_text = """Pros:
1. Direct integration
2. Focus on accessibility and consistency.
**Cons**:
1. Potential overlap
2. Requires navigating and configuring docs
## A heading
- A new bullet
- Another bullet"""
    test_markdown_roundtrip(word_document, markdown_text)


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
    test_markdown_roundtrip(word_document, markdown_text)


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
    test_markdown_roundtrip(word_document, markdown_text)


def test_comments(word_document):
    markdown_text = """## Market Opportunity
Here are the market opportunities:
<!-- This is a comment -->
- Growing Market: The market is projected to grow.
- Target Audience: Our primary customers are enterprises.
Let's get into the details."""
    test_markdown_roundtrip(word_document, markdown_text)


def test_comments_inside_list(word_document):
    markdown_text = """## Market Opportunity
Here are the market opportunities:
- Growing Market: The market is projected to grow.
<!-- This is a comment -->
- Target <!-- second comment --> Audience: Our primary customers are enterprises.
Let's get into the details."""
    test_markdown_roundtrip(word_document, markdown_text)


def test_comments_consecutive(word_document):
    markdown_text = """## Market Opportunity
Here are the market opportunities:
- Growing Market: The market is projected to grow.
<!-- This is a comment -->
<!-- second comment -->

- Target Audience: Our primary customers are enterprises.
Let's get into the details."""
    test_markdown_roundtrip(word_document, markdown_text)


def test_comments_inside_code(word_document):
    markdown_text = """- item 1
- item 2
- item 3
```python
a = 2
b = 3
<!-- This is a comment -->
total = a + b
if total > 4:
    print(f"Hello, the answer is {a + b}")

```
#### This is a heading 4
1. item 1
1. item 2
And here is a regular paragraph"""
    test_markdown_roundtrip(word_document, markdown_text)


def test_comments_long(word_document):
    markdown_text = """<!-- comment at the start of the doc --> ## Option 1

<!-- This is a comment that is very long and should be split into multiple lines to ensure that it does not exceed the maximum line length. This is important for readability and maintainability of the code. -->
<!-- second comment! -->
<!-- This is another comment that we want to have preserved in the markdown. It should also be long enough to test thoroughly. -->

### Overview
Fluent UI, developed by Microsoft, embodies the design language of Microsoft 365 and emphasizes \
accessibility and consistent user experiences. When merged with Tailwind CSS—a utility-first, highly \
flexible styling framework—this approach allows for rapid style customization and a tailored \
layout that meets both brand standards and modern design expectations.

This combination not only enhances user experience but also ensures that applications are visually appealing and functional.
"""
    test_markdown_roundtrip(word_document, markdown_text)


def test_comments_near_end(word_document):
    markdown_text = """## Market Opportunity
Here are the market opportunities:
- Growing Market: The market is projected to grow.
- Target Audience: Our primary customers are enterprises.
Let's get into the <!-- comment at the end --> details.<!-- comment after all text on the same line - not preserved -->
<!-- Comment actually at the end of the doc - not preserved -->"""
    # NOTE: Comments at the very end of the document are not preserved in the markdown.
    test_markdown_roundtrip(word_document, markdown_text)
