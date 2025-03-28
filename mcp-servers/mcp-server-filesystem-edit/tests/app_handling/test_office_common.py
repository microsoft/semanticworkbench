import sys
from pathlib import Path

import pytest
from mcp_server_filesystem_edit.app_handling.office_common import (
    OfficeAppType,
    open_document_in_office,
)


@pytest.fixture(autouse=True)
def check_for_win():
    if sys.platform != "win32":
        pytest.skip("This test is only applicable on Windows.")


def test_open_word(word_file_path: Path) -> None:
    _, doc = open_document_in_office(word_file_path, OfficeAppType.WORD)
    assert doc is not None

    _, doc = open_document_in_office(word_file_path, OfficeAppType.WORD)
    assert doc is not None


def test_open_powerpoint(ppt_file_path: Path) -> None:
    _, doc = open_document_in_office(ppt_file_path, OfficeAppType.POWERPOINT)
    assert doc is not None
