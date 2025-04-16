from pathlib import Path

import pytest


@pytest.fixture
def temporary_directory() -> Path:
    path = Path(__file__).parents[1] / "temp" / "tests"
    path.mkdir(parents=True, exist_ok=True)
    return path


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
