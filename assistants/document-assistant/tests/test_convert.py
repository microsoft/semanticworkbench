from pathlib import Path

from assistant.filesystem._convert import bytes_to_str

SAMPLE_FILE_DIR = Path(__file__).parent / "test_data"
SAMPLE_DOCX = SAMPLE_FILE_DIR / "Formatting Test.docx"
SAMPLE_PDF = SAMPLE_FILE_DIR / "simple_pdf.pdf"
SAMPLE_PPTX = SAMPLE_FILE_DIR / "sample_presentation.pptx"
SAMPLE_PNG = SAMPLE_FILE_DIR / "blank_image.png"
SAMPLE_CSV = SAMPLE_FILE_DIR / "sample_data.csv"
SAMPLE_XLSX = SAMPLE_FILE_DIR / "sample_data.xlsx"
SAMPLE_HTML = SAMPLE_FILE_DIR / "sample_page.html"


async def test_docx_bytes_to_str() -> None:
    expected_result = """# My Heading 1

This is a simple word document to test

### My Heading 3

This is bulleted list:

* Item 1
* Item 2"""
    result = await bytes_to_str(SAMPLE_DOCX.read_bytes(), SAMPLE_DOCX.name)
    assert result == expected_result


async def test_pdf_bytes_to_str() -> None:
    expected_result = """My Heading 1
This is a simple PDF document to test.
My Heading 3
This is bulleted list:
- Item 1
- Item 2"""
    result = await bytes_to_str(SAMPLE_PDF.read_bytes(), SAMPLE_PDF.name)
    assert result == expected_result


async def test_pptx_bytes_to_str() -> None:
    expected_result = """<!-- Slide number: 1 -->
# Slide 1
This is a simple PowerPoint presentation to test

<!-- Slide number: 2 -->
# Slide 2
This is bulleted list:
Item 1
Item 2

<!-- Slide number: 3 -->
# Image Slide with text

![simple_plot_pptx.png](Picture2.jpg)
Some text relating to the image

<!-- Slide number: 4 -->
# Table Slide
| Col 1 | Col 2 | Col 3 |
| --- | --- | --- |
| A | B | C |
| D | E | F |"""

    result = await bytes_to_str(SAMPLE_PPTX.read_bytes(), SAMPLE_PPTX.name)
    assert result == expected_result


async def test_image_bytes_to_str() -> None:
    result = await bytes_to_str(SAMPLE_PNG.read_bytes(), SAMPLE_PNG.name)
    # assert it starts with data:png;base64
    assert result.startswith("data:image/png;base64,")


async def test_csv_bytes_to_str() -> None:
    expected_result = """Name,Age,Department,Salary
Alice,30,HR,50000
Bob,24,Engineering,70000
Charlie,29,Marketing,60000
"""
    result = await bytes_to_str(SAMPLE_CSV.read_bytes(), SAMPLE_CSV.name)
    assert result == expected_result


async def test_xlsx_bytes_to_str() -> None:
    expected_result = """## Sheet1
| Name | Age | Department | Salary |
| --- | --- | --- | --- |
| Alice | 30 | HR | 50000 |
| Bob | 24 | Engineering | 70000 |
| Charlie | 29 | Marketing | 60000 |"""
    result = await bytes_to_str(SAMPLE_XLSX.read_bytes(), SAMPLE_XLSX.name)
    assert result == expected_result


async def test_html_bytes_to_str() -> None:
    expected_result = """# My Heading 1

This is a simple HTML page to test.

### My Heading 3

This is a bulleted list:

* Item 1
* Item 2

![Simple Line Plot](simple_plot_html.png)"""
    result = await bytes_to_str(SAMPLE_HTML.read_bytes(), SAMPLE_HTML.name)
    assert result == expected_result
