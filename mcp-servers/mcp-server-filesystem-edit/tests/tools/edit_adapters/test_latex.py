# Copyright (c) Microsoft. All rights reserved.

from mcp_server_filesystem_edit.tools.edit_adapters.latex import (
    blockify,
    find_math_blocks,
    find_preamble,
    find_sections,
    unblockify,
)

# Test LaTeX document sections
PREAMBLE = r"""\documentclass[12pt]{article}
\usepackage{amsmath}
\usepackage{graphicx}
\title{Sample Document}
\author{Author Name}
\date{\today}
"""

DOCUMENT_START = r"""\begin{document}
\maketitle
"""

SECTION_1 = r"""\section{Introduction}
This is the introduction to the document. It contains some basic text.
"""

EQUATION = r"""\begin{equation}
E = mc^2
\end{equation}
"""

ITEMIZE = r"""\begin{itemize}
\item First item
\item Second item
\item Third item
\end{itemize}
"""

FIGURE = r"""\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{image.png}
\caption{A sample image}
\label{fig:sample}
\end{figure}
"""

SECTION_2 = r"""\section{Methodology}
This section describes the methodology.

This is a separate paragraph in the methodology section.
"""

MATH_DISPLAY = r"""\[
\int_{0}^{\infty} e^{-x^2} dx = \frac{\sqrt{\pi}}{2}
\]
"""

DOCUMENT_END = r"""\end{document}
"""

# Create a complete LaTeX document for testing
COMPLETE_LATEX = (
    PREAMBLE + DOCUMENT_START + SECTION_1 + EQUATION + ITEMIZE + FIGURE + SECTION_2 + MATH_DISPLAY + DOCUMENT_END
)


def test_find_sections():
    """Test that sections are correctly identified."""
    sections = find_sections(COMPLETE_LATEX)
    assert len(sections) == 2  # Introduction and Methodology


def test_find_math_blocks():
    """Test that math blocks are correctly identified."""
    math_blocks = find_math_blocks(COMPLETE_LATEX)
    assert len(math_blocks) == 2  # equation environment and display math


def test_find_preamble():
    """Test that the preamble is correctly identified."""
    preamble = find_preamble(COMPLETE_LATEX)
    assert len(preamble) == 1


def test_blockify_complete():
    """Test blockify on a complete LaTeX document."""
    blocks = blockify(COMPLETE_LATEX)
    assert len(blocks) > 0
    # First block should be the preamble
    assert "\\documentclass" in blocks[0].content
    # Last block should contain document end
    assert "\\end{document}" in blocks[-1].content


def test_blockify_roundtrip():
    """Test that blockify followed by unblockify returns the original text."""
    blocks = blockify(COMPLETE_LATEX)
    reconstructed = unblockify(blocks)
    assert reconstructed == COMPLETE_LATEX


def test_small_document():
    """Test with a small document."""
    small_doc = r"""\documentclass{article}
\begin{document}
Hello world!
\end{document}"""
    blocks = blockify(small_doc)
    assert len(blocks) >= 2  # At least preamble and document content
    assert unblockify(blocks) == small_doc


def test_document_with_paragraphs():
    """Test that paragraphs are properly separated."""
    doc_with_paragraphs = r"""\documentclass{article}
\begin{document}
First paragraph text.

Second paragraph text.

Third paragraph with
multiple lines.
\end{document}"""
    blocks = blockify(doc_with_paragraphs)
    assert unblockify(blocks) == doc_with_paragraphs


if __name__ == "__main__":
    test_find_sections()
    test_find_math_blocks()
    test_find_preamble()
    test_blockify_complete()
    test_blockify_roundtrip()
    test_small_document()
    test_document_with_paragraphs()
