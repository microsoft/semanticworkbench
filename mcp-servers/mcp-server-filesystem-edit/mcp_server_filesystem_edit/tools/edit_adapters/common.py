# Copyright (c) Microsoft. All rights reserved.

from copy import deepcopy
from typing import Any

from mcp_server_filesystem_edit.types import Block


async def format_blocks_for_llm(blocks: list[Block]) -> str:
    """A string representation of the canvas used for prompting an LLM.
    The string returned is as follows:
    <block index=0>
    start_of_document_indicator
    </block>
    <block index={idx}>
    content
    </block>
    <block index={idx}>
    content
    </block>
    ...
    """
    page = """<block index=0>
start_of_document_indicator
</block>
"""
    for block in blocks:
        markdown_content = block.content
        # Remove one trailing newline, if it exists
        markdown_content = markdown_content[:-1] if markdown_content.endswith("\n") else markdown_content
        page += f"""<block index={block.id}>
{markdown_content}
</block>\n"""
    page = page.rstrip()
    return page


def execute_tools(
    blocks: list[Block],
    edit_tool_call: Any,
) -> list[Block]:
    """Executes the tools called by the LLM and returns the new blockified page.
    NOTE: We add a newline to generated content so it is unblockified as expected.
    """
    new_block_id = -5
    blocks = deepcopy(blocks)
    tools = edit_tool_call.get("arguments", {}).get("operations", [])
    for tool in tools:
        # INSERT LOGIC
        # 1. Find the index, or the first index after (in the case the targeted block was deleted), the model generated.
        # 2. Execute a "prepend" operation by finding the next block in the mapping
        #    that is not a newly inserted block and prepend before that block.
        # 3. If we do not find the next block in the mapping (meaning the index chosen was the last), we append to the end.
        if tool["type"] == "insert":
            # Find the the block at the generated index
            try:
                index = int(tool["index"])
            except ValueError:
                index = 0

            # Any index less than 0 assume the intent was the append at the beginning
            if index < 0:
                index = 0

            block_inserted = False
            for i, block in enumerate(deepcopy(blocks)):
                # Iterate until we find the next block one index greater than the model generated
                if block.id > index:
                    # This would be translated to the prepend operation to insert
                    # the block before the next block with the id in the mapping.
                    content = tool["content"] + "\n"
                    blocks.insert(
                        i,  # Prepend
                        Block(
                            id=new_block_id,
                            content=content,
                        ),
                    )

                    block_inserted = True
                    break

            if not block_inserted:
                # Append to the end (translates into the append at end operation)
                content = tool["content"] + "\n"
                blocks.append(
                    Block(
                        id=new_block_id,
                        content=content,
                    ),
                )
        elif tool["type"] == "update":
            # UPDATE LOGIC
            # 1. Find the block at the index the model generated.
            # 2. Replace the current content with the new content.
            try:
                index = int(tool["index"])
            except ValueError:
                continue
            if index <= 0:
                continue

            content = tool["content"] + "\n"
            for block in blocks:
                if block.id == index:
                    block.content = content
                    break
        elif tool["type"] == "remove":
            # REMOVE LOGIC
            # 1. Remove all blocks between the start_index and end_index (inclusive).
            try:
                start_index = int(tool["start_index"])
                end_index = int(tool["end_index"])
            except ValueError:
                continue

            if start_index <= 0 or end_index <= 0:
                continue

            blocks = [block for block in blocks if not (start_index <= block.id <= end_index)]

    return blocks
