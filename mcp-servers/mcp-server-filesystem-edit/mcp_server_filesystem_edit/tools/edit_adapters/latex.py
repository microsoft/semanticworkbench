# Copyright (c) Microsoft. All rights reserved.

import re

from mcp_server_filesystem_edit.types import Block


def find_sections(text: str) -> list[tuple[int, int]]:
    """Finds the start and end indices of section commands in LaTeX.

    Matches section commands like \section{}, \subsection{}, etc.
    """
    # Match section commands and their content
    pattern = r"\\(?:sub)*(?:section|chapter|part|paragraph)\{[^}]*\}"

    sections = []
    for match in re.finditer(pattern, text):
        sections.append((match.start(), match.end()))

    return sections


def find_math_blocks(text: str) -> list[tuple[int, int]]:
    """Finds the start and end indices of math blocks in LaTeX.

    Matches display math environments and equation environments.
    """
    # Match various math delimiters: $$..$$, \[..\], \begin{equation}...\end{equation}, etc.
    patterns = [
        r"\$\$(.*?)\$\$",  # $$...$$
        r"\\\[(.*?)\\\]",  # \[...\]
        r"\\begin\{equation\}(.*?)\\end\{equation\}",  # equation environment
        r"\\begin\{align\*?\}(.*?)\\end\{align\*?\}",  # align environment
    ]

    math_blocks = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.DOTALL):
            math_blocks.append((match.start(), match.end()))

    return math_blocks


def find_preamble(text: str) -> list[tuple[int, int]]:
    """Finds the preamble section of a LaTeX document."""
    doc_class_match = re.search(r"\\documentclass(\[.*?\])?\{.*?\}", text)
    begin_doc_match = re.search(r"\\begin\{document\}", text)

    if doc_class_match and begin_doc_match:
        return [(doc_class_match.start(), begin_doc_match.start())]
    return []


def combine_overlapping_blocks(blocks: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Combines overlapping blocks into a single block."""
    if not blocks:
        return []

    # Sort blocks by start position
    sorted_blocks = sorted(blocks)

    combined = []
    current_start, current_end = sorted_blocks[0]
    for start, end in sorted_blocks[1:]:
        if start <= current_end:
            # If blocks overlap extend current block
            current_end = max(current_end, end)
        else:
            # No overlap, add current block and start a new one
            combined.append((current_start, current_end))
            current_start, current_end = start, end

    # Add the last block
    combined.append((current_start, current_end))

    return combined


def fill_gaps_blocks(blocks: list[tuple[int, int]], text_length: int) -> list[tuple[int, int]]:
    """Fills in the gaps between blocks from beginning to end of text."""
    if not blocks:
        return [(0, text_length)]

    blocks = sorted(blocks)
    missing_blocks = []
    last_end = 0

    for start, end in blocks:
        if last_end < start:
            missing_blocks.append((last_end, start))
        last_end = end

    if last_end < text_length:
        missing_blocks.append((last_end, text_length))

    return missing_blocks


def combine_newline_blocks(blocks: list[tuple[int, int]], text: str) -> list[tuple[int, int]]:
    """Combines blocks that are just a newline with the previous block."""
    if not blocks:
        return []

    new_blocks = []
    i = 0
    while i < len(blocks):
        current_start, current_end = blocks[i]

        # Look ahead for newline blocks
        while (
            i + 1 < len(blocks)
            and blocks[i + 1][1] - blocks[i + 1][0] == 1  # Check if the block is length 1
            and text[blocks[i + 1][0] : blocks[i + 1][1]] == "\n"  # Block is a newline
        ):
            current_end = blocks[i + 1][1]
            i += 1

        new_blocks.append((current_start, current_end))
        i += 1

    return new_blocks


def blockify(latex_text: str) -> list[Block]:
    """Converts LaTeX text into an ordered list of blocks.

    This divides a LaTeX document into logical blocks based on:
    1. Environments (like figure, table, itemize)
    2. Section commands
    3. Math blocks
    4. Preamble
    5. Other text is split into paragraphs
    """
    # Find all the structured blocks
    # environment_blocks = find_environments(latex_text)
    section_blocks = find_sections(latex_text)
    math_blocks = find_math_blocks(latex_text)
    preamble_blocks = find_preamble(latex_text)

    # Combine all structured blocks
    all_structured_blocks = section_blocks + math_blocks + preamble_blocks

    # Combine overlapping blocks
    combined_blocks = combine_overlapping_blocks(all_structured_blocks)

    # Fill in gaps between structured blocks
    gap_blocks = fill_gaps_blocks(combined_blocks, len(latex_text))

    # Combine all blocks and sort by position
    all_blocks = sorted(combined_blocks + gap_blocks)

    # Combine lone newlines with previous blocks
    all_blocks = combine_newline_blocks(all_blocks, latex_text)

    # Convert to Block objects
    blocks_output = []
    for idx, (start, end) in enumerate(all_blocks):
        blocks_output.append(
            Block(
                id=idx + 1,
                content=latex_text[start:end],
            )
        )

    return blocks_output


def unblockify(blocks: list[Block]) -> str:
    """Converts a list of blocks back into LaTeX text."""
    return "".join(block.content for block in blocks)
