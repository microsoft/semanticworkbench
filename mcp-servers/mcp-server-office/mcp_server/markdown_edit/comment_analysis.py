# Copyright (c) Microsoft. All rights reserved.

import json

import pendulum

from mcp_server.app_interaction.word_editor import (
    get_active_document,
    get_document_comments,
    get_markdown_representation,
    get_word_app,
)
from mcp_server.constants import FEEDBACK_ASSISTANT_PREFIX
from mcp_server.helpers import compile_messages, format_chat_history
from mcp_server.llm.chat_completion import chat_completion
from mcp_server.prompts.comment_analysis import COMMENT_ANALYSIS_MESSAGES, COMMENT_ANALYSIS_SCHEMA
from mcp_server.types import (
    ChatCompletionRequest,
    CommentAnalysisData,
    CommentAnalysisOutput,
    CustomContext,
    MarkdownEditRequest,
    UserMessage,
)


async def run_comment_analysis(markdown_edit_request: MarkdownEditRequest) -> CommentAnalysisOutput:
    """
    Analyzes the comments in the Word document to determine if they are actionable or not.
    If they are, it generates edit instructions.
    If they are not, it generates a "hint" to send to the assistant to indicate what would be needed to address the comment.
    """
    word = get_word_app()
    doc = get_active_document(word)

    if markdown_edit_request.request_type == "dev":
        comments = markdown_edit_request.context.comments  # type: ignore
    else:
        comments = get_document_comments(doc)

    if markdown_edit_request.request_type == "dev" and isinstance(markdown_edit_request.context, CustomContext):
        markdown_from_word = markdown_edit_request.context.document
    else:
        markdown_from_word = get_markdown_representation(doc, include_comments=True)

    context = ""
    if markdown_edit_request.request_type == "dev" and isinstance(markdown_edit_request.context, CustomContext):
        context = markdown_edit_request.context.additional_context

    chat_history = ""
    if markdown_edit_request.request_type == "dev" and isinstance(markdown_edit_request.context, CustomContext):
        chat_history = format_chat_history(markdown_edit_request.context.chat_history)

    edit_instructions = ""
    assistant_hints = ""
    analysis_messages = compile_messages(
        messages=COMMENT_ANALYSIS_MESSAGES,
        variables={
            "knowledge_cutoff": "2023-10",
            "current_date": pendulum.now().format("YYYY-MM-DD"),
            "context": context,
            "chat_history": chat_history,
            "document": markdown_from_word,
        },
    )
    if markdown_edit_request.request_type == "mcp":
        messages = [analysis_messages[0]]  # Developer message
        messages.append(UserMessage(content=json.dumps({"variable": "attachment_messages"})))
        messages.append(UserMessage(content=json.dumps({"variable": "history_messages"})))
        messages.append(analysis_messages[3])  # Document message
        messages.extend(markdown_edit_request.additional_messages)  # Possible messages from previous steps
        analysis_messages = messages

    analysis_response = await chat_completion(
        request=ChatCompletionRequest(
            messages=analysis_messages,
            model="gpt-4o",
            max_completion_tokens=8000,
            temperature=0.5,
            structured_outputs=COMMENT_ANALYSIS_SCHEMA,
        ),
        provider=markdown_edit_request.request_type,
        client=markdown_edit_request.context
        if markdown_edit_request.request_type == "mcp"
        else markdown_edit_request.chat_completion_client,  # type: ignore
    )
    comment_analysis = analysis_response.choices[0].json_message

    comment_analysis_data: list[CommentAnalysisData] = []
    if comment_analysis:
        for comment in comment_analysis.get("comment_analysis", []):
            comment_id = comment.get("comment_id", None)
            if comment_id is None:
                continue
            else:
                try:
                    comment_id = int(comment_id) - 1
                except ValueError:
                    continue
            comment_analysis_data.append(
                CommentAnalysisData(
                    comment_data=comments[comment_id],
                    output_message=comment.get("output_message", ""),
                    necessary_context_reasoning=comment.get("necessary_context_reasoning", ""),
                    is_actionable=comment.get("is_actionable", False),
                )
            )
        # Convert to edit instructions and final instructions string
        for comment_data in comment_analysis_data:
            if comment_data.is_actionable:
                edit_str = f'To address the comment "{comment_data.comment_data.comment_text}" at location "{comment_data.comment_data.location_text}", please do the following:'
                edit_instructions += f"{edit_str}\n{comment_data.output_message}\n\n"
            else:
                assistant_str = f'To address the comment "{comment_data.comment_data.comment_text}" at location "{comment_data.comment_data.location_text}":'
                assistant_hints += f"{assistant_str}\n{comment_data.output_message}\n\n"

    if edit_instructions:
        edit_instructions = f"{FEEDBACK_ASSISTANT_PREFIX} {edit_instructions}"
        edit_instructions = edit_instructions.strip()

    if assistant_hints:
        assistant_hints = f"{FEEDBACK_ASSISTANT_PREFIX} {assistant_hints}"
        assistant_hints = assistant_hints.strip()

    output = CommentAnalysisOutput(
        edit_instructions=edit_instructions,
        assistant_hints=assistant_hints,
        json_message=comment_analysis or {},
        comment_analysis=comment_analysis_data,
    )
    return output
