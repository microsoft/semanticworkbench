# Copyright (c) Microsoft. All rights reserved.

import pendulum
from mcp.server.fastmcp import Context

from mcp_server.app_interaction.word_editor import (
    get_active_document,
    get_markdown_representation,
    get_word_app,
    write_markdown_to_document,
)
from mcp_server.constants import CHANGE_SUMMARY_PREFIX, DEFAULT_DOC_EDIT_TASK
from mcp_server.helpers import compile_messages
from mcp_server.llm.chat_completion import chat_completion
from mcp_server.markdown_edit.utils import blockify, construct_page_for_llm, execute_tools, unblockify
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
    AssistantMessage,
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    CustomContext,
    Function,
    MarkdownEditOutput,
    MarkdownEditRequest,
    MessageT,
    ToolCall,
)


async def run_markdown_edit(markdown_edit_request: MarkdownEditRequest) -> MarkdownEditOutput:
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

    blockified_doc = blockify(markdown_from_word)
    doc_for_llm = construct_page_for_llm(blockified_doc)

    # Convert chat history to a string if we are in Dev mode
    chat_history = ""
    if markdown_edit_request.request_type == "dev" and isinstance(markdown_edit_request.context, CustomContext):
        chat_history = format_chat_history(markdown_edit_request.context.chat_history)

    context = ""
    if markdown_edit_request.request_type == "dev" and isinstance(markdown_edit_request.context, CustomContext):
        context = markdown_edit_request.context.additional_context

    # endregion

    # region Reasoning step
    # This is necessary since o3-mini-high is much more capable at page edits,
    # but not very good at tool calls so we split it up into two steps.

    reasoning_messages = compile_messages(
        messages=MD_EDIT_REASONING_MESSAGES,
        variables={
            "knowledge_cutoff": "2023-10",
            "current_date": pendulum.now().format("YYYY-MM-DD"),
            "task": DEFAULT_DOC_EDIT_TASK,
            "context": context,
            "document": doc_for_llm,
            "chat_history": chat_history,
        },
    )
    if markdown_edit_request.request_type == "mcp" and isinstance(markdown_edit_request.context, Context):
        reasoning_response = await chat_completion(
            request=ChatCompletionRequest(
                messages=reasoning_messages,
                model="gpt-4o",
                max_completion_tokens=8000,
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

    # endregion

    # region Convert step
    # This converts reasoning to tool calls

    convert_messages = compile_messages(
        messages=MD_EDIT_CONVERT_MESSAGES,
        variables={"reasoning": reasoning},
    )
    if markdown_edit_request.request_type == "mcp":
        # TODO: Sampling to get the tool calls from gpt-4o
        function_args = {
            "operations": [{"type": "insert", "index": "100", "content": "Wait, there's more! Let us keep editing"}]
        }
        convert_response = ChatCompletionResponse(
            choices=[
                ChatCompletionChoice(
                    message=AssistantMessage(
                        content="",
                        tool_calls=[
                            ToolCall(id="call_abc", function=Function(name="doc_edit", arguments=function_args))
                        ],
                    ),
                    finish_reason="stop",
                ),
            ],
            completion_tokens=0,
            prompt_tokens=0,
            response_duration=0,
        )
    elif markdown_edit_request.request_type == "dev":
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
            provider="azure_openai",
            client=markdown_edit_request.chat_completion_client,  # type: ignore
        )
    else:
        raise ValueError(f"Invalid request type: {markdown_edit_request.request_type}")

    # endregion

    # region Execute step
    # Now that we have the tool calls, we can execute them in Word
    # We also generate a change summary to output back to the assistant.

    updated_doc_markdown = markdown_from_word
    change_summary = ""
    output_message = ""
    if convert_response.choices[0].message.tool_calls:
        tool_call = convert_response.choices[0].message.tool_calls[0].function
        # If the the model called the send_message, don't update the doc and return the message
        if tool_call.name == SEND_MESSAGE_TOOL_NAME:
            output_message = convert_response.choices[0].message.content
        elif tool_call.name == MD_EDIT_TOOL_NAME:
            tool_args = tool_call.arguments
            blocks = blockify(updated_doc_markdown)
            blocks = execute_tools(blocks=blocks, edit_tool_call={"name": tool_call.name, "arguments": tool_args})
            updated_doc_markdown = unblockify(blocks)
            write_markdown_to_document(doc, updated_doc_markdown)
            del doc, word
            if updated_doc_markdown != markdown_from_word:
                change_summary = await run_change_summary(
                    before_doc=markdown_from_word,
                    after_doc=updated_doc_markdown,
                    markdown_edit_request=markdown_edit_request,
                )
            else:
                change_summary = "No changes were made to the document."
    else:
        output_message = "Something went wrong when editing the document and no changes were made."

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
    if markdown_edit_request.request_type == "mcp" and isinstance(markdown_edit_request.context, Context):
        change_summary = await chat_completion(
            request=ChatCompletionRequest(
                messages=change_summary_messages,
                model="gpt-4o",
                max_completion_tokens=1000,
            ),
            provider="mcp",
            client=markdown_edit_request.context,
        )
        change_summary = change_summary.choices[0].message.content
    elif markdown_edit_request.request_type == "dev":
        request = ChatCompletionRequest(
            messages=change_summary_messages,
            model="gpt-4o",
            max_completion_tokens=1000,
        )
        change_summary = await chat_completion(
            request=request,
            provider="azure_openai",
            client=markdown_edit_request.chat_completion_client,  # type: ignore
        )
        change_summary = change_summary.choices[0].message.content
    else:
        raise ValueError(f"Invalid request type: {markdown_edit_request.request_type}")

    change_summary = CHANGE_SUMMARY_PREFIX + change_summary
    return change_summary


# endregion


# region Helpers


def format_chat_history(chat_history: list[MessageT]) -> str:
    formatted_chat_history = ""
    for message in chat_history:
        formatted_chat_history += f"[{message.role.value}]: {message.content}\n"
    return formatted_chat_history.strip()


# endregion
