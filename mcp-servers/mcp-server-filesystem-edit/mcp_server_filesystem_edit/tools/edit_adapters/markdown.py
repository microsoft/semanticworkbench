# Copyright (c) Microsoft. All rights reserved.

import re

from mcp_server_filesystem_edit.types import Block


def find_tables(text: str) -> list[tuple[int, int]]:
    """Finds the start and end indices of tables in a string.

    An example of the table syntax is as follows:
    |Column 1|Column 2|
    |A|B|
    |C|D|
    |D|D|

    Notice that it is non-standard markdown.
    """
    pattern = r"^\|[^\n|]+\|(?:[^\n|]+\|)*$(?:\n\|.+\|)*"

    tables = []
    # Using re.MULTILINE to make ^ and $ match line boundaries
    for match in re.finditer(pattern, text, re.MULTILINE):
        tables.append((match.start(), match.end()))

    return tables


def find_code_blocks(text: str) -> list[tuple[int, int]]:
    """Finds the start and end indices of all code block in a string.
    A code block is delimited by ```\n and \n```.
    """
    pattern = r"```.*?\n(.*?\n)```"
    matches = list(re.finditer(pattern, text, re.DOTALL))
    return [(m.start(), m.end()) for m in matches]


def find_lists(text: str) -> list[tuple[int, int]]:
    """Finds the start and end indices of all lists in a string."""
    # Pattern matches a line starting with "1. " or "- " (with optional leading spaces)
    pattern = r"(?m)^[ ]*(?:1\.|\-)[ ].+"

    lists = []
    matches = list(re.finditer(pattern, text))
    if not matches:
        return []

    current_start = matches[0].start()
    current_end = matches[0].end()

    # Extend the end position for each consecutive list item
    for match in matches[1:]:
        if match.start() - current_end <= 1:
            current_end = match.end()
        else:
            lists.append((current_start, current_end))
            current_start = match.start()
            current_end = match.end()

    lists.append((current_start, current_end))
    return lists


def find_comments(text: str) -> list[tuple[int, int]]:
    """Finds the start and end indices of HTML comments in a Markdown string.

    HTML comments in Markdown have the form <!-- comment text -->.
    They can span multiple lines.
    """
    pattern = r"<!--(.*?)-->"
    matches = list(re.finditer(pattern, text, re.DOTALL))
    return [(m.start(), m.end()) for m in matches]


def combine_overlapping_blocks(blocks: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Combines overlapping blocks into a single block.

    Example:
    Input: [(5, 15), (15, 20), (0, 10)]
    Output: [(0, 20)]

    Example 2:
    Input: [(0, 10), (11, 20), (15, 25)]
    Output: [(0, 10), (11, 25)]
    """
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
    """Fills in the missing blocks between the given blocks from the
    beginning of the text to the end of the text and returns those blocks

    Example:
        Input: [(11, 20), (25, 30)], length = 40
        Output: [(0, 11), (11, 20), (20, 25), (25, 30), (30, 40)]
    """
    missing_blocks = []
    last_end = 0
    for start, end in blocks:
        if last_end < start:
            missing_blocks.append((last_end, start))
        last_end = end

    if last_end < text_length:
        missing_blocks.append((last_end, text_length))

    return missing_blocks


def split_blocks_by_newlines(blocks: list[tuple[int, int]], text: str) -> list[tuple[int, int]]:
    """Splits the given blocks by newlines and returns the new blocks."""
    new_blocks = []
    for start, end in blocks:
        current_start = start
        current_text = text[start:end]
        lines = current_text.splitlines()

        for line in lines:
            # + 1 to account for the newline character
            line_length = len(line) + 1
            new_blocks.append((current_start, current_start + line_length))
            current_start += line_length

    return new_blocks


def combine_newline_blocks(blocks: list[tuple[int, int]], text: str) -> list[tuple[int, int]]:
    """Combines blocks that are just a newline with the previous block."""
    new_blocks = []
    i = 0
    while i < len(blocks):
        current_start, current_end = blocks[i]
        # Look ahead for newline blocks
        while (
            i + 1 < len(blocks)
            and blocks[i + 1][1] - blocks[i + 1][0] == 1  # Check if the block is length 1
            and text[blocks[i + 1][0] : blocks[i + 1][1]] == "\n"
        ):  # Block is a newline
            current_end = blocks[i + 1][1]
            i += 1

        new_blocks.append((current_start, current_end))
        i += 1

    return new_blocks


def combine_heading_blocks(blocks: list[tuple[int, int]], text: str) -> list[tuple[int, int]]:
    """Combines blocks that are headings with the next block."""
    new_blocks = []
    i = 0
    while i < len(blocks):
        start, end = blocks[i]
        content = text[start:end]

        # Check if current block is a heading
        if re.match(r"^#{1,3}\s", content.lstrip()) and (i + 1 < len(blocks)):
            _, next_end = blocks[i + 1]
            new_blocks.append((start, next_end))
            i += 2  # Skip the next block since we combined it
            continue

        # Not a heading or no next block to combine with
        new_blocks.append((start, end))
        i += 1

    return new_blocks


def blockify(markdown_text: str) -> list[Block]:
    """Converts markdown text into an ordered list of blocks which have an identified and content.
    This representation should preserve exactly the markdown text when unblockified.

    1. Use find_tables, find_code_blocks, and find_lists to find blocks corresponding to those common things that should be treated as blocks.
    2. The remaining text to create paragraph blocks.
    3. Consolidate headings and paragraphs by considering any text that immediately follows a heading as part of that heading's block.
    """

    table_blocks = find_tables(markdown_text)
    code_blocks = find_code_blocks(markdown_text)
    list_blocks = find_lists(markdown_text)
    comment_blocks = find_comments(markdown_text)

    # Combine blocks that overlap into a single block
    combined_blocks = combine_overlapping_blocks(table_blocks + code_blocks + list_blocks + comment_blocks)

    # Fill in the missing blocks
    filled_blocks = fill_gaps_blocks(combined_blocks, len(markdown_text))

    # For each remaining block, split the corresponding text by newlines and add the resulting blocks to the remaining blocks.
    filled_blocks = split_blocks_by_newlines(filled_blocks, markdown_text)
    # Sort blocks by start position
    blocks = sorted(combined_blocks + filled_blocks)

    # Any block that is just a newline, combine it with the previous block
    blocks = combine_newline_blocks(blocks, markdown_text)
    # Any block that is a heading, combine it with the next block
    blocks = combine_heading_blocks(blocks, markdown_text)

    # Convert blocks into a list of Block models
    blocks_output = []
    for idx, (start, end) in enumerate(blocks):
        blocks_output.append(
            Block(
                id=idx + 1,
                content=markdown_text[start:end],
            )
        )
    # If there is a missing newline at the end of the document, add one
    if len(blocks_output) > 0 and not blocks_output[-1].content.endswith("\n"):
        blocks_output[-1].content = blocks_output[-1].content + "\n"
    return blocks_output


def unblockify(blocks: list[Block]) -> str:
    """Converts a list of blocks back into markdown text."""
    return "".join(block.content for block in blocks)
