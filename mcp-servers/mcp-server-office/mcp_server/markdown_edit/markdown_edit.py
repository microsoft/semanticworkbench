# Copyright (c) Microsoft. All rights reserved.

import json

import pendulum

from mcp_server.app_interaction.word_editor import (
    get_active_document,
    get_markdown_representation,
    get_word_app,
    write_markdown_to_document,
)
from mcp_server.constants import CHANGE_SUMMARY_PREFIX, DEFAULT_DOC_EDIT_TASK
from mcp_server.helpers import compile_messages
from mcp_server.markdown_edit.utils import blockify, construct_page_for_llm, execute_tools, unblockify
from mcp_server.prompts.markdown_edit import (
    MD_EDIT_CHANGES_MESSAGES,
    MD_EDIT_CONVERT_MESSAGES,
    MD_EDIT_REASONING_MESSAGES,
    MD_EDIT_TOOL_NAME,
    SEND_MESSAGE_TOOL_NAME,
)


def run_markdown_edit(chat_history: str, additional_context: str | None = None) -> str:
    """
    Run the markdown edit.
    """
    # Get Markdown representation of the currently open Word document
    word = get_word_app()
    doc = get_active_document(word)
    markdown_from_word = get_markdown_representation(doc)

    blockified_doc = blockify(markdown_from_word)
    doc_for_llm = construct_page_for_llm(blockified_doc)

    reasoning_messages = compile_messages(
        messages=MD_EDIT_REASONING_MESSAGES,
        variables={
            "knowledge_cutoff": "2023-10",
            "current_date": pendulum.now().format("YYYY-MM-DD"),
            "task": DEFAULT_DOC_EDIT_TASK,
            "context": additional_context or "",
            "document": doc_for_llm,
            "chat_history": chat_history,
        },
    )

    # TODO: Sampling - Get the reasoning from o3-mini-high using MCP Sampling
    reasoning = "HARD CODED REASONING FOR NOW"

    convert_messages = compile_messages(
        messages=MD_EDIT_CONVERT_MESSAGES,
        variables={"reasoning": reasoning},
    )

    # TODO: Sampling to get the tool calls from gpt-4o
    convert_response = {
        "choices": [
            {
                "message": {
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "call_abc",
                            "function": {
                                "name": "doc_edit",
                                "arguments": '{"operations": [{"type": "insert", "index": "1", "content": "This is a sample inserted content."}]}',
                            },
                        }
                    ],
                },
            }
        ],
    }
    updated_doc_markdown = markdown_from_word
    change_summary = ""
    output_message = ""

    if convert_response["choices"][0]["message"]["tool_calls"]:
        tool_call = convert_response["choices"][0]["message"]["tool_calls"][0]["function"]
        # If the the model called the send_message, don't update the doc and return the message
        if tool_call["name"] == SEND_MESSAGE_TOOL_NAME:
            output_message = convert_response["choices"][0]["message"]["content"]
        elif tool_call["name"] == MD_EDIT_TOOL_NAME:
            tool_call["arguments"] = json.loads(tool_call["arguments"])
            blocks = blockify(updated_doc_markdown)
            blocks = execute_tools(blocks=blocks, edit_tool_call=tool_call)  # type: ignore
            updated_doc_markdown = unblockify(blocks)
            write_markdown_to_document(doc, updated_doc_markdown)
            del doc, word
            if updated_doc_markdown != markdown_from_word:
                change_summary = run_change_summary(
                    before_doc=markdown_from_word,
                    after_doc=updated_doc_markdown,
                )
            else:
                change_summary = "No changes were made to the document."
    else:
        output_message = "Something went wrong when editing the document and no changes were made."

    return change_summary or output_message


def run_change_summary(before_doc: str, after_doc: str) -> str:
    change_summary_messages = compile_messages(
        messages=MD_EDIT_CHANGES_MESSAGES,
        variables={
            "before_doc": before_doc,
            "after_doc": after_doc,
        },
    )
    # TODO: Sampling to get the change summary from gpt-4o using MCP Sampling

    change_summary = CHANGE_SUMMARY_PREFIX + "HARD CODED SUMMARY"
    return change_summary
