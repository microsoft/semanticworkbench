import tempfile
from pathlib import Path
from typing import Iterator

import pytest


@pytest.fixture
def temporary_directory() -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        temp_path.mkdir(exist_ok=True, parents=True)
        yield temp_path


@pytest.fixture
def word_file_path(temporary_directory: Path) -> Path:
    return temporary_directory / "test_document.docx"


@pytest.fixture
def excel_file_path(temporary_directory: Path) -> Path:
    return temporary_directory / "test_book.xlsx"


@pytest.fixture
def ppt_file_path(temporary_directory: Path) -> Path:
    return temporary_directory / "test_presentation.pptx"


@pytest.fixture
def csv_file_path(temporary_directory: Path) -> Path:
    return temporary_directory / "test_book.csv"
