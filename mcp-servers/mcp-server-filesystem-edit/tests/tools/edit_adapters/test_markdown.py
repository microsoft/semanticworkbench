# Copyright (c) Microsoft. All rights reserved.

from mcp_server_filesystem_edit.tools.edit_adapters.markdown import (
    blockify,
    combine_overlapping_blocks,
    find_code_blocks,
    find_lists,
    find_tables,
    unblockify,
)

TABLE_1 = """|Page Title|Description|Features|
|The Bear and the Magic Lamp|Ideas for a story| |
|Greatest Games Article|Top 5 greatest sports games of all time| |
|Guided Conversation Ideas|Notes on a project| |
|Azure VM Setup|Loose notes on setting up a new VM in Azure for development| |
|Cloud LLM Comparison|Comparing AWS to Azure features||
|Dashboard - Meeting Notes|Fake meeting notes for two meetings| |
|Performance Benchmark Suite in Rust|||"""

TABLE_2 = """|Column 1|Column 2|
|A|B|
|C|D|
|D|D|
"""

TABLE_TEXT_1 = f"""# Heading 1
{TABLE_1}"""

TABLE_TEXT_2 = f"""Some text
{TABLE_2}
Some more text"""

TABLE_TEXT_3 = f"""```
{TABLE_2}
```"""

TABLE_TEXT_4 = f"""This is a paragraph.
## Heading 2
### Heading 3

{TABLE_1}

{TABLE_2}

This is some more text.
"""

TABLE_TEXT_5 = f"""{TABLE_2}
## Heading 2
### Heading 3
{TABLE_1}

{TABLE_2}
This is some more text."""


def test_find_tables_1():
    result = find_tables(TABLE_TEXT_1)
    assert len(result) == 1
    assert result[0] == (12, 452)


def test_find_tables_2():
    result = find_tables(TABLE_TEXT_2)
    assert len(result) == 1
    assert result[0] == (10, 47)


def test_find_tables_3():
    result = find_tables(TABLE_TEXT_3)
    assert len(result) == 1
    assert result[0] == (4, 41)


def test_find_tables_4():
    result = find_tables(TABLE_TEXT_4)
    assert len(result) == 2
    assert result[0] == (49, 489)
    assert result[1] == (491, 528)


def test_find_tables_5():
    result = find_tables(TABLE_TEXT_5)
    assert len(result) == 3
    assert result[0] == (0, 37)
    assert result[1] == (66, 506)
    assert result[2] == (508, 545)


CODE_BLOCK_1 = """```Python
print(\"hello world\")
a = 2
```"""

CODE_BLOCK_2 = """```Python
print(\"hello world again!\")
a = 3
a = 4
```"""

CODE_BLOCK_3 = """```Python

print(\"hello world once again!\")
a = 10

```"""

CODE_TEXT_1 = f"""{CODE_BLOCK_1}"""

CODE_TEXT_2 = f"""Here is a code block
{CODE_BLOCK_2}"""

CODE_TEXT_3 = f"""### CODE
{CODE_BLOCK_3}
|Column 1|Column 2|
|A|B|
|C|D|
|D|D|
This some text"""

CODE_TEXT_4 = f"""## This is a Heading
{CODE_BLOCK_1}
{CODE_BLOCK_2}
This is some text
Hello
{CODE_BLOCK_3}
"""


def test_find_code_blocks_1():
    result = find_code_blocks(CODE_TEXT_1)
    assert len(result) == 1
    assert result[0] == (0, len(CODE_TEXT_1))


def test_find_code_blocks_2():
    result = find_code_blocks(CODE_TEXT_2)
    assert len(result) == 1
    assert result[0] == (21, len(CODE_TEXT_2))


def test_find_code_blocks_3():
    result = find_code_blocks(CODE_TEXT_3)
    assert len(result) == 1
    assert result[0] == (9, 64)


def test_find_code_blocks_4():
    result = find_code_blocks(CODE_TEXT_4)
    assert len(result) == 3
    assert result[0] == (21, 61)
    assert result[1] == (62, 115)
    assert result[2] == (140, 195)


LIST_1 = """1. hello!"""

LIST_2 = """1. first item
1. second item
  1. nested second item
1. third item"""

LIST_3 = """- item 1
- item 2
  - nested item 3
    - double tested item 4
- item 5"""

LIST_4 = """1. mixed list 1
  - nested item 1
  - nested item 2
1. mixed list 2"""

LIST_5 = """- 2 list 1
- 2 list 2
  - 2 nested 1
  - 2 nested 2"""

LIST_TEXT_1 = f"""{LIST_4}"""

LIST_TEXT_2 = f"""Hello!
{LIST_2}
```Python
print("hello world once again!")
a = 10
```
{LIST_5}"""

LIST_TEXT_3 = f"""{LIST_2}
{LIST_4}
Hello!



"""


LIST_TEXT_4 = f"""{LIST_2}
## This is a Heading
This is some text
{LIST_3}
Hello
{LIST_1}

{LIST_4}
```Python

print(\"hello world once again!\")
a = 10

```
{LIST_5}
"""


def test_find_lists_1():
    result = find_lists(LIST_TEXT_1)
    assert len(result) == 1
    assert result[0] == (0, len(LIST_TEXT_1))


def test_find_lists_2():
    result = find_lists(LIST_TEXT_2)
    assert len(result) == 2
    assert result[0] == (7, 73)
    assert result[1] == (128, len(LIST_TEXT_2))


def test_find_lists_3():
    result = find_lists(LIST_TEXT_3)
    assert len(result) == 1
    assert result[0] == (0, 134)


def test_find_lists_4():
    result = find_lists(LIST_TEXT_4)
    assert len(result) == 5
    assert result[0] == (0, 66)
    assert result[1] == (106, 177)
    assert result[2] == (184, 193)
    assert result[3] == (195, 262)
    assert result[4] == (319, 370)


def test_combine_overlapping_blocks_1():
    result = combine_overlapping_blocks([(5, 15), (15, 20), (0, 10)])
    assert result == [(0, 20)]


def test_combine_overlapping_blocks_2():
    result = combine_overlapping_blocks([(0, 10), (11, 20), (15, 25)])
    assert result == [(0, 10), (11, 25)]


MARKDOWN_TEXT = markdown_text = """## Introduction
Markdown is a lightweight markup language that allows you to create formatted text using a plain-text editor. It is widely used for documentation, notes, and content creation.

This is another paragraph.

This is a third paragraph.
## Features of Markdown
- **Simplicity**: Easy to learn and use.
- **Portability**: Supported in many applications and platforms.
- **Flexibility**: Can include headings, tables, lists, and more.
## Syntax Examples
### Headings
Use `#` symbols to define headings:
- `#` for H1
- `##` for H2
- `###` for H3
Example:
```markdown
# This is a Heading 1
## This is a Heading 2
### This is a Heading 3
```


"""


def test_blockify_roundtrip():
    blocks = blockify(markdown_text)
    rt_markdown_text = unblockify(blocks)
    assert rt_markdown_text == markdown_text


if __name__ == "__main__":
    test_find_code_blocks_1()
    test_find_code_blocks_2()
    test_find_code_blocks_3()
    test_find_code_blocks_4()

    test_find_tables_1()
    test_find_tables_2()
    test_find_tables_3()
    test_find_tables_4()
    test_find_tables_5()

    test_find_lists_1()
    test_find_lists_2()
    test_find_lists_3()
    test_find_lists_4()

    test_combine_overlapping_blocks_1()
    test_combine_overlapping_blocks_2()

    test_blockify_roundtrip()
