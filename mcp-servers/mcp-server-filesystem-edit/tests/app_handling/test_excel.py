import sys
from pathlib import Path

import pytest
from mcp_server_filesystem_edit.app_handling.excel import get_worksheet_content_as_md_table
from mcp_server_filesystem_edit.app_handling.office_common import OfficeAppType, open_document_in_office


@pytest.fixture(autouse=True)
def check_for_win():
    if sys.platform != "win32":
        pytest.skip("This test is only applicable on Windows.")


def test_get_worksheet_content(excel_file_path: Path):
    _, doc = open_document_in_office(excel_file_path, OfficeAppType.EXCEL)
    empty_worksheet = get_worksheet_content_as_md_table(doc)
    print(empty_worksheet)


def test_get_worksheet_content_csv(csv_file_path: Path):
    _, doc = open_document_in_office(csv_file_path, OfficeAppType.EXCEL)
    empty_worksheet = get_worksheet_content_as_md_table(doc)
    print(empty_worksheet)
