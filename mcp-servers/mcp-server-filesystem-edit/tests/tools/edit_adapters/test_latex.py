# Copyright (c) Microsoft. All rights reserved.

from mcp_server_filesystem_edit.tools.edit_adapters.latex import (
    blockify,
    unblockify,
)
from pathlib import Path
from rich import print

TEST_FILE_PATH = Path(__file__).parents[3] / "data" / "attachments" / "Research Template.tex"


def test_blockify_roundtrip():
    """Test that blockify followed by unblockify returns the original text."""
    latex_content = TEST_FILE_PATH.read_text(encoding="utf-8")

    blocks = blockify(latex_content)
    print(blocks)
    reconstructed = unblockify(blocks)
    assert reconstructed == latex_content

def test_small_document():
    small_doc = r"""\documentclass{article}
\begin{document}
Hello world!
\end{document}"""
    blocks = blockify(small_doc)
    assert len(blocks) >= 3
    assert unblockify(blocks) == small_doc

