from pathlib import Path

from mcp_server_filesystem_edit.app_handling.office_common import (
    OfficeAppType,
    open_document_in_office,
)

TEMP_FILES_PATH = Path(__file__).parents[2] / "temp" / "tests"
TEMP_FILES_PATH.mkdir(exist_ok=True)
WORD_FILE = TEMP_FILES_PATH / "test_document.docx"
EXCEL_FILE = TEMP_FILES_PATH / "test_book.xlsx"
PPT_FILE = TEMP_FILES_PATH / "test_presentation.pptx"


def test_open_word() -> None:
    _, doc = open_document_in_office(WORD_FILE, OfficeAppType.WORD)
    assert doc is not None


def test_open_excel() -> None:
    _, doc = open_document_in_office(EXCEL_FILE, OfficeAppType.EXCEL)
    assert doc is not None


def test_open_powerpoint() -> None:
    _, doc = open_document_in_office(PPT_FILE, OfficeAppType.POWERPOINT)
    assert doc is not None
