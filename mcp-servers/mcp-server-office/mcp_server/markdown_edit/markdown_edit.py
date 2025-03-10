# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json
import logging

import pendulum
from liquid import Template
from mcp.server.fastmcp import Context

from mcp_server.app_interaction.word_editor import (
    get_active_document,
    get_comments_markdown_representation,
    get_markdown_representation,
    get_word_app,
    write_markdown_to_document,
)
from mcp_server.constants import CHANGE_SUMMARY_PREFIX, DEFAULT_DOC_EDIT_TASK, DEFAULT_DRAFT_TASK
from mcp_server.helpers import compile_messages, format_chat_history
from mcp_server.llm.chat_completion import chat_completion
from mcp_server.markdown_edit.utils import (
    blockify,
    construct_page_for_llm,
    execute_tools,
    strip_horizontal_rules,
    unblockify,
)
from mcp_server.prompts.markdown_draft import MD_DRAFT_REASONING_MESSAGES
from mcp_server.prompts.markdown_edit import (
    MD_EDIT_CHANGES_MESSAGES,
    MD_EDIT_CONVERT_MESSAGES,
    MD_EDIT_REASONING_MESSAGES,
    MD_EDIT_TOOL_DEF,
    MD_EDIT_TOOL_NAME,
    SEND_MESSAGE_TOOL_DEF,
    SEND_MESSAGE_TOOL_NAME,
)
from mcp_server.types import (
    ChatCompletionRequest,
    CustomContext,
    MarkdownEditOutput,
    MarkdownEditRequest,
    UserMessage,
)

logger = logging.getLogger(__name__)


async def run_markdown_edit(
    markdown_edit_request: MarkdownEditRequest,
) -> MarkdownEditOutput:
    """
    Run the markdown edit.
    """
    # region Preparing context

    # Get Markdown representation of the currently open Word document
    word = get_word_app()
    doc = get_active_document(word)
    if markdown_edit_request.request_type == "dev" and isinstance(markdown_edit_request.context, CustomContext):
        markdown_from_word = markdown_edit_request.context.document
    else:
        markdown_from_word = get_markdown_representation(doc)

    # If the document is empty, take a separate path that directly writes a draft.
    if not markdown_from_word.strip():
        return await run_markdown_draft(markdown_edit_request, doc)

    blockified_doc = blockify(markdown_from_word)
    doc_for_llm = construct_page_for_llm(blockified_doc)
    doc_for_llm += get_comments_markdown_representation(doc)

    # Convert chat history to a string if we are in Dev mode
    chat_history = ""
    if markdown_edit_request.request_type == "dev" and isinstance(markdown_edit_request.context, CustomContext):
        chat_history = format_chat_history(markdown_edit_request.context.chat_history)

    context = ""
    if markdown_edit_request.request_type == "dev" and isinstance(markdown_edit_request.context, CustomContext):
        context = markdown_edit_request.context.additional_context

    if markdown_edit_request.task != DEFAULT_DOC_EDIT_TASK:
        task = Template(DEFAULT_DOC_EDIT_TASK).render(task=markdown_edit_request.task)
    else:
        task = Template(DEFAULT_DOC_EDIT_TASK).render(task="")

    # endregion

    # region Reasoning step
    # This is necessary since o3-mini-high is much more capable at page edits,
    # but not very good at tool calls so we split it up into two steps.

    reasoning_messages = compile_messages(
        messages=MD_EDIT_REASONING_MESSAGES,
        variables={
            "knowledge_cutoff": "2023-10",
            "current_date": pendulum.now().format("YYYY-MM-DD"),
            "task": task,
            "context": context,
            "document": doc_for_llm,
            "chat_history": chat_history,
        },
    )
    if markdown_edit_request.request_type == "mcp" and isinstance(markdown_edit_request.context, Context):
        messages = [reasoning_messages[0]]  # Developer message
        messages.append(UserMessage(content=json.dumps({"variable": "attachment_messages"})))
        messages.append(UserMessage(content=json.dumps({"variable": "history_messages"})))
        messages.append(reasoning_messages[3])  # Document message
        messages.extend(markdown_edit_request.additional_messages)  # Possible messages from previous steps
        reasoning_response = await chat_completion(
            request=ChatCompletionRequest(
                messages=messages,
                model="o3-mini",
                max_completion_tokens=20000,
                reasoning_effort="high",
            ),
            provider="mcp",
            client=markdown_edit_request.context,
        )
    elif markdown_edit_request.request_type == "dev":
        reasoning_response = await chat_completion(
            request=ChatCompletionRequest(
                messages=reasoning_messages,
                model="o3-mini",
                max_completion_tokens=20000,
                reasoning_effort="high",
            ),
            provider="azure_openai",
            client=markdown_edit_request.chat_completion_client,  # type: ignore
        )
    else:
        raise ValueError(f"Invalid request type: {markdown_edit_request.request_type}")
    reasoning = reasoning_response.choices[0].message.content
    logging.info(f"Reasoning:\n{reasoning}")

    # endregion

    # region Convert step
    # This converts reasoning to tool calls

    convert_messages = compile_messages(
        messages=MD_EDIT_CONVERT_MESSAGES,
        variables={"reasoning": reasoning},
    )
    request = ChatCompletionRequest(
        messages=convert_messages,
        model="gpt-4o",
        temperature=0,
        max_completion_tokens=8000,
        tools=[MD_EDIT_TOOL_DEF, SEND_MESSAGE_TOOL_DEF],
        tool_choice="required",
        parallel_tool_calls=False,
    )
    convert_response = await chat_completion(
        request=request,
        provider=markdown_edit_request.request_type,
        client=markdown_edit_request.context
        if markdown_edit_request.request_type == "mcp"
        else markdown_edit_request.chat_completion_client,  # type: ignore
    )

    # endregion

    # region Execute step
    # Now that we have the tool calls, we can execute them in Word
    # We also generate a change summary to output back to the assistant.

    updated_doc_markdown = markdown_from_word
    change_summary = ""
    output_message = ""
    if convert_response.choices[0].message.tool_calls:
        tool_call = convert_response.choices[0].message.tool_calls[0].function
        logging.info(f"Tool call:\n{tool_call}")
        # If the the model called the send_message, don't update the doc and return the message
        if tool_call.name == SEND_MESSAGE_TOOL_NAME:
            output_message = CHANGE_SUMMARY_PREFIX + convert_response.choices[0].message.content
        elif tool_call.name == MD_EDIT_TOOL_NAME:
            tool_args = tool_call.arguments
            blocks = blockify(updated_doc_markdown)
            logging.info(f"Blocks (before modifications):\n{blocks}")
            blocks = execute_tools(blocks=blocks, edit_tool_call={"name": tool_call.name, "arguments": tool_args})
            updated_doc_markdown = unblockify(blocks)
            updated_doc_markdown = strip_horizontal_rules(updated_doc_markdown)

            if updated_doc_markdown != markdown_from_word:
                change_summary_task = asyncio.create_task(
                    run_change_summary(
                        before_doc=markdown_from_word,
                        after_doc=updated_doc_markdown,
                        markdown_edit_request=markdown_edit_request,
                    )
                )
                write_markdown_to_document(doc, updated_doc_markdown)
                change_summary = await change_summary_task
            else:
                change_summary = CHANGE_SUMMARY_PREFIX + "No changes were made to the document."
    else:
        output_message = (
            CHANGE_SUMMARY_PREFIX + "Something went wrong when editing the document and no changes were made."
        )

    # endregion

    output = MarkdownEditOutput(
        change_summary=change_summary,
        output_message=output_message,
        new_markdown=updated_doc_markdown,
        reasoning=reasoning,
        tool_calls=convert_response.choices[0].message.tool_calls or [],
        llm_latency=convert_response.response_duration + reasoning_response.response_duration,
    )
    return output


# region Change summary


async def run_change_summary(before_doc: str, after_doc: str, markdown_edit_request: MarkdownEditRequest) -> str:
    change_summary_messages = compile_messages(
        messages=MD_EDIT_CHANGES_MESSAGES,
        variables={
            "before_doc": before_doc,
            "after_doc": after_doc,
        },
    )
    change_summary = await chat_completion(
        request=ChatCompletionRequest(
            messages=change_summary_messages,
            model="gpt-4o",
            max_completion_tokens=1000,
        ),
        provider=markdown_edit_request.request_type,
        client=markdown_edit_request.context
        if markdown_edit_request.request_type == "mcp"
        else markdown_edit_request.chat_completion_client,  # type: ignore
    )
    change_summary = change_summary.choices[0].message.content
    change_summary = CHANGE_SUMMARY_PREFIX + change_summary
    return change_summary


# endregion

# region Markdown draft


async def run_markdown_draft(markdown_edit_request: MarkdownEditRequest, doc) -> MarkdownEditOutput:
    # Convert chat history to a string if we are in Dev mode
    chat_history = ""
    if markdown_edit_request.request_type == "dev" and isinstance(markdown_edit_request.context, CustomContext):
        chat_history = format_chat_history(markdown_edit_request.context.chat_history)

    context = ""
    if markdown_edit_request.request_type == "dev" and isinstance(markdown_edit_request.context, CustomContext):
        context = markdown_edit_request.context.additional_context

    if markdown_edit_request.task != DEFAULT_DRAFT_TASK:
        task = Template(DEFAULT_DRAFT_TASK).render(task=markdown_edit_request.task)
    else:
        task = Template(DEFAULT_DOC_EDIT_TASK).render(task="")

    draft_messages = compile_messages(
        messages=MD_DRAFT_REASONING_MESSAGES,
        variables={
            "knowledge_cutoff": "2023-10",
            "current_date": pendulum.now().format("YYYY-MM-DD"),
            "task": task,
            "context": context,
            "chat_history": chat_history,
        },
    )

    if markdown_edit_request.request_type == "mcp" and isinstance(markdown_edit_request.context, Context):
        messages = [draft_messages[0]]  # Developer message
        messages.append(UserMessage(content=json.dumps({"variable": "attachment_messages"})))
        messages.append(UserMessage(content=json.dumps({"variable": "history_messages"})))
        response = await chat_completion(
            request=ChatCompletionRequest(
                messages=messages,
                model="o3-mini",
                max_completion_tokens=20000,
                reasoning_effort="high",
            ),
            provider="mcp",
            client=markdown_edit_request.context,  # type: ignore
        )
    elif markdown_edit_request.request_type == "dev":
        response = await chat_completion(
            request=ChatCompletionRequest(
                messages=draft_messages,
                model="o3-mini",
                max_completion_tokens=20000,
                reasoning_effort="high",
            ),
            provider="azure_openai",
            client=markdown_edit_request.chat_completion_client,  # type: ignore
        )
    else:
        raise ValueError(f"Invalid request type: {markdown_edit_request.request_type}")

    markdown_draft = response.choices[0].message.content
    markdown_draft = strip_horizontal_rules(markdown_draft)

    change_summary_task = asyncio.create_task(
        run_change_summary(
            before_doc="",
            after_doc=markdown_draft,
            markdown_edit_request=markdown_edit_request,
        )
    )
    write_markdown_to_document(doc, markdown_draft)
    change_summary = await change_summary_task

    output = MarkdownEditOutput(
        change_summary=change_summary,
        output_message="",
        new_markdown=markdown_draft,
        reasoning="",
        tool_calls=[],
        llm_latency=response.response_duration,
    )
    return output


# endregion
