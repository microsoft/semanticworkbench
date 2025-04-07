# Copyright (c) Microsoft. All rights reserved.

import re

from mcp_server_filesystem_edit.types import Block


def find_documentclass(text: str) -> list[tuple[int, int]]:
    """Find \\documentclass commands in LaTeX text."""
    pattern = r"\\documentclass(\[.*?\])?\{.*?\}(\n)?"
    return [(m.start(), m.end()) for m in re.finditer(pattern, text)]


def find_usepackage_blocks(text: str) -> list[tuple[int, int]]:
    """Find consecutive \\usepackage commands and group them together."""
    pattern = r"\\usepackage(\[.*?\])?\{.*?\}(\n)?"
    matches = list(re.finditer(pattern, text))

    if not matches:
        return []

    blocks = []
    current_start = matches[0].start()
    current_end = matches[0].end()

    for i in range(1, len(matches)):
        # If there's only whitespace/newlines between this match and the previous one,
        # extend the current block
        gap_text = text[current_end : matches[i].start()]
        if re.match(r"^[\s\n]*$", gap_text):
            current_end = matches[i].end()
        else:
            blocks.append((current_start, current_end))
            current_start = matches[i].start()
            current_end = matches[i].end()

    blocks.append((current_start, current_end))
    return blocks


def find_document_tags(text: str) -> list[tuple[int, int]]:
    """Find \\begin{document} and \\end{document} commands."""
    blocks = []

    begin_match = re.search(r"\\begin\{document\}", text)
    if begin_match:
        blocks.append((begin_match.start(), begin_match.end()))

    end_match = re.search(r"\\end\{document\}", text)
    if end_match:
        blocks.append((end_match.start(), end_match.end()))

    return blocks


def find_sections(text: str) -> list[tuple[int, int]]:
    """Find section, subsection, and subsubsection commands and their content."""
    # Find all section commands
    pattern = r"\\(section|subsection|subsubsection)(\[.*?\])?\{.*?\}"
    section_matches = list(re.finditer(pattern, text))

    if not section_matches:
        return []

    blocks = []
    for i in range(len(section_matches) - 1):
        start = section_matches[i].start()
        end = section_matches[i + 1].start()
        blocks.append((start, end))

    # Handle the last section (extends to the end of document or \end{document})
    if section_matches:
        last_start = section_matches[-1].start()
        end_doc_match = re.search(r"\\end\{document\}", text)
        if end_doc_match:
            blocks.append((last_start, end_doc_match.start()))
        else:
            blocks.append((last_start, len(text)))

    return blocks


def find_environments(text: str, env_type: str) -> list[tuple[int, int]]:
    """Find complete LaTeX environments of the given type."""
    pattern = rf"\\begin\{{{env_type}.*?\}}.*?\\end\{{{env_type}.*?\}}"
    return [(m.start(), m.end()) for m in re.finditer(pattern, text, re.DOTALL)]


def find_tables(text: str) -> list[tuple[int, int]]:
    """Find table environments in LaTeX."""
    table_blocks = find_environments(text, "table")
    tabular_blocks = find_environments(text, "tabular")
    return table_blocks + tabular_blocks


def find_lists(text: str) -> list[tuple[int, int]]:
    """Find itemize and enumerate environments in LaTeX."""
    itemize_blocks = find_environments(text, "itemize")
    enumerate_blocks = find_environments(text, "enumerate")
    return itemize_blocks + enumerate_blocks


def handle_overlapping_blocks(blocks: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Resolves overlapping blocks by splitting them at overlap boundaries.

    Instead of merging overlapping blocks into a single large block, this function
    splits blocks at their points of intersection, creating smaller non-overlapping
    blocks that cover the same text regions.

    Args:
        blocks: List of (start, end) tuples representing text blocks

    Returns:
        List of non-overlapping (start, end) tuples covering the same text regions
    """
    if not blocks:
        return []

    # Convert blocks to a set of boundary points with labels:
    # +1 for a start point, -1 for an end point
    boundaries = []
    for start, end in blocks:
        boundaries.append((start, +1))
        boundaries.append((end, -1))

    # Sort boundaries by position
    boundaries.sort()

    result = []
    current_depth = 0
    last_position = None

    for position, direction in boundaries:
        # If we had an active segment and position changed
        if current_depth > 0 and last_position is not None and position > last_position:
            result.append((last_position, position))

        # Update depth counter
        current_depth += direction
        last_position = position

    return result


def fill_gaps(blocks: list[tuple[int, int]], text_length: int) -> list[tuple[int, int]]:
    """Fill gaps between blocks and ensure full text coverage."""
    if not blocks:
        return [(0, text_length)]

    sorted_blocks = sorted(blocks)
    result = []
    last_end = 0

    for start, end in sorted_blocks:
        if start > last_end:
            result.append((last_end, start))
        result.append((start, end))
        last_end = end

    if last_end < text_length:
        result.append((last_end, text_length))

    return result


def merge_small_blocks(
    blocks: list[tuple[int, int]], min_size: int = 50, preserve_num: int = 3
) -> list[tuple[int, int]]:
    """Merge blocks smaller than min_size with the previous block.

    The first 3 blocks and last 3 blocks are preserved regardless of size to maintain
    document structure (preamble and closing elements).

    Args:
        blocks: List of (start, end) tuples representing text blocks
        min_size: Minimum block size in characters before merging with previous block
        preserve_num: Number of blocks to preserve at the start and end of the document

    Returns:
        List of (start, end) tuples with small blocks merged where appropriate
    """
    if len(blocks) <= 1:
        return blocks

    # If we have 2*preserve_num or fewer blocks, just return them unchanged
    # since all would be in the "preserved" category
    if len(blocks) <= 2 * preserve_num:
        return blocks

    # Calculate the range of blocks eligible for merging
    preserve_start = preserve_num
    preserve_end = len(blocks) - preserve_num

    # Keep the first preserve_num blocks as is
    result = blocks[:preserve_start]

    # Process middle blocks that are eligible for merging
    for i in range(preserve_start, preserve_end):
        current_start, current_end = blocks[i]
        current_size = current_end - current_start

        if current_size < min_size:
            # Merge with previous block
            prev_start, _ = result[-1]
            result[-1] = (prev_start, current_end)
        else:
            result.append((current_start, current_end))

    # Add the remaining blocks from the end (to be preserved)
    result.extend(blocks[preserve_end:])

    return result


def blockify(latex_text: str) -> list[Block]:
    """
    Converts LaTeX text into an ordered list of blocks. Ensures that the entire string is covered
    so that unblockify can be used to losslessly reconstruct the original string.

    This divides a LaTeX document into logical blocks based on:
    1. documentclass is in its own block
    2. consecutive usepackage commands are in the same block
    3. begin{document} and end{document} is in its own block
    4. section, subsection, and subsubsection are in their own blocks until the next section
    5. entire tables are in their own blocks
    6. Entire lists are in their own blocks (itemize or enumerate)
    7. Gaps in between blocks constructed up to this point are filled in with their own blocks
    8. All other text is in its own block
    9. Blocks that are contain less than 100 characters are merged with the previous block
    """
    # Find all block types
    documentclass_blocks = find_documentclass(latex_text)
    usepackage_blocks = find_usepackage_blocks(latex_text)
    document_blocks = find_document_tags(latex_text)
    section_blocks = find_sections(latex_text)
    table_blocks = find_tables(latex_text)
    list_blocks = find_lists(latex_text)

    # Combine all identified blocks
    all_blocks = (
        documentclass_blocks + usepackage_blocks + document_blocks + section_blocks + table_blocks + list_blocks
    )

    # Fill in the gaps to ensure complete coverage
    all_blocks = fill_gaps(all_blocks, len(latex_text))

    # Handle overlapping blocks by splitting at intersection points
    all_blocks = handle_overlapping_blocks(all_blocks)

    # Merge small blocks with their predecessor
    all_blocks = merge_small_blocks(all_blocks)

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
    """
    Converts a list of blocks back into LaTeX text.
    """
    return "".join(block.content for block in blocks)
