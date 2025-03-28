# Copyright (c) Microsoft. All rights reserved.

# This assumes that `pdflatex` is installed and available in the PATH.

from pathlib import Path

import pytest
from mcp_server_filesystem_edit.app_handling.miktex import compile_tex_to_pdf

SAMPLE_TEX_PATH = Path(__file__).parents[2] / "data" / "attachments" / "Research Template.tex"


def test_miktex() -> None:
    """
    Test the MikTeX functionality.
    """
    pytest.skip("This test is skipped because it requires a working MikTeX installation.")
    success, output = compile_tex_to_pdf(SAMPLE_TEX_PATH)
    assert success, f"Compilation failed with output: {output}"
    pdf_file = SAMPLE_TEX_PATH.with_suffix(".pdf")
    assert pdf_file.exists(), f"PDF file was not created: {pdf_file}"
