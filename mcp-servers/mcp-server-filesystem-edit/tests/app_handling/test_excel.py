from pathlib import Path

from mcp_server_filesystem_edit.app_handling.excel import get_worksheet_content_as_md_table
from mcp_server_filesystem_edit.app_handling.office_common import OfficeAppType, open_document_in_office

TEMP_FILES_PATH = Path(__file__).parents[2] / "temp" / "tests"
EXCEL_FILE = TEMP_FILES_PATH / "test_book.xlsx"
CSV_FILE = TEMP_FILES_PATH / "test_book.csv"


def test_get_worksheet_content():
    _, doc = open_document_in_office(EXCEL_FILE, OfficeAppType.EXCEL)
    empty_worksheet = get_worksheet_content_as_md_table(doc)
    print(empty_worksheet)


def test_get_worksheet_content_csv():
    _, doc = open_document_in_office(CSV_FILE, OfficeAppType.EXCEL)
    empty_worksheet = get_worksheet_content_as_md_table(doc)
    print(empty_worksheet)
