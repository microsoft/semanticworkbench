import sys
from pathlib import Path

import pytest
from mcp_server_filesystem_edit.app_handling.office_common import OfficeAppType, open_document_in_office
from mcp_server_filesystem_edit.app_handling.powerpoint import (
    get_markdown_representation,
    write_markdown,
)


@pytest.fixture(autouse=True)
def check_for_win():
    if sys.platform != "win32":
        pytest.skip("This test is only applicable on Windows.")


@pytest.fixture
def powerpoint_document(ppt_file_path: Path):
    """Fixture that provides an active PowerPoint document."""
    _, doc = open_document_in_office(ppt_file_path, OfficeAppType.POWERPOINT)
    yield doc


def markdown_roundtrip_helper(powerpoint_document, markdown_text: str) -> str:
    """
    Helper function that performs a roundtrip test:
    1. Writes markdown to a PowerPoint document
    2. Reads it back as markdown
    3. Writes the read markdown back to the document
    """
    write_markdown(powerpoint_document, markdown_text)
    rt_markdown_text = get_markdown_representation(powerpoint_document)
    write_markdown(powerpoint_document, rt_markdown_text)
    return rt_markdown_text


def test_title_and_content(powerpoint_document):
    markdown_text = """<slide num=<3> layout="title_and_content">
<title>Key Points</title>
<content>
## Main Ideas
- First important point
- Second important point
- Third important point with **bold text** in the middle
## Additional Information
1. Numbered item one
2. Numbered item two with *italic text*
</content>
</slide>"""
    markdown_roundtrip_helper(powerpoint_document, markdown_text)


def test_formatting(powerpoint_document):
    markdown_text = """<slide num=<3> layout="title_and_content">
<title>Key Points</title>
<content>
important point with **bold text** in the middle
</content>
</slide>"""
    markdown_roundtrip_helper(powerpoint_document, markdown_text)


def test_section_header(powerpoint_document):
    markdown_text = """<slide num=<2> layout="section_header">
<title>Agenda</title>
<content>
What we'll cover today
</content>
</slide>"""
    markdown_roundtrip_helper(powerpoint_document, markdown_text)


def test_title(powerpoint_document):
    markdown_text = """<slide num=<1> layout="title">
<title>Presentation Title</title>
<content>By **John** Smith</content>
</slide>"""
    markdown_roundtrip_helper(powerpoint_document, markdown_text)


def test_basic_presentation_content(powerpoint_document):
    markdown_text = """<slide num=<1> layout="title">
<title>Presentation Title</title>
<content>By John Smith</content>
</slide>

<slide num=<2> layout="section_header">
<title>Agenda</title>
<content>
What we'll cover today
</content>
</slide>

<slide num=<3> layout="title_and_content">
<title>Key Points</title>
<content>
## Main Ideas
- First important point
- Second important point
- Third important point with **bold text**

## Additional Information
1. Numbered item one
2. Numbered item two with *italic text*
</content>
</slide>

<slide num=<4> layout="two_content">
<title>Comparison</title>
<content>
### Option A
- Feature 1
- Feature 2
- Feature 3
</content>
<content>
### Option B
- Alternative 1
- Alternative 2
- ***Important note***
</content>
</slide>
"""
    markdown_roundtrip_helper(powerpoint_document, markdown_text)
