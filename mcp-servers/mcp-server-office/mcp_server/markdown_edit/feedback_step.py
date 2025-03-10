# Copyright (c) Microsoft. All rights reserved.

import json
import logging

import pendulum

from mcp_server.app_interaction.word_editor import (
    add_document_comment,
    get_active_document,
    get_markdown_representation,
    get_word_app,
)
from mcp_server.helpers import compile_messages, format_chat_history
from mcp_server.llm.chat_completion import chat_completion
from mcp_server.prompts.feedback import (
    FEEDBACK_CONVERT_MESSAGES,
    FEEDBACK_MESSAGES,
    FEEDBACK_TOOL_DEF,
    FEEDBACK_TOOL_NAME,
)
from mcp_server.types import (
    ChatCompletionRequest,
    CustomContext,
    FeedbackOutput,
    MarkdownEditRequest,
    UserMessage,
    WordCommentData,
)


async def run_feedback_step(markdown_edit_request: MarkdownEditRequest) -> FeedbackOutput:
    """
    Applies comments to the Word document
    """
    # region Preparing context
    word = get_word_app()
    doc = get_active_document(word)
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

    # endregion

    # region Feedback Reasoning
    feedback_messages = compile_messages(
        messages=FEEDBACK_MESSAGES,
        variables={
            "knowledge_cutoff": "2023-10",
            "current_date": pendulum.now().format("YYYY-MM-DD"),
            "context": context,
            "document": markdown_from_word,
            "chat_history": chat_history,
        },
    )
    if markdown_edit_request.request_type == "mcp":
        # Specially format messages for use with MCP
        messages = [feedback_messages[0]]  # Developer message
        messages.append(UserMessage(content=json.dumps({"variable": "attachment_messages"})))
        messages.append(UserMessage(content=json.dumps({"variable": "history_messages"})))
        messages.append(feedback_messages[3])  # Document message
        messages.extend(markdown_edit_request.additional_messages)  # Possible messages from previous steps
        feedback_messages = messages

    feedback_response = await chat_completion(
        request=ChatCompletionRequest(
            messages=feedback_messages,
            model="o3-mini",
            max_completion_tokens=15000,
            reasoning_effort="medium",
        ),
        provider=markdown_edit_request.request_type,
        client=markdown_edit_request.context
        if markdown_edit_request.request_type == "mcp"
        else markdown_edit_request.chat_completion_client,  # type: ignore
    )
    feedback_reasoning = feedback_response.choices[0].message.content
    logging.info(f"Feedback:\n{feedback_reasoning}")

    # endregion

    # region Apply Feedback

    feedback_convert_messages = compile_messages(
        messages=FEEDBACK_CONVERT_MESSAGES,
        variables={"reasoning": feedback_reasoning},
    )
    request = ChatCompletionRequest(
        messages=feedback_convert_messages,
        model="gpt-4o",
        temperature=0,
        max_completion_tokens=8000,
        tools=[FEEDBACK_TOOL_DEF],
        tool_choice="required",
        parallel_tool_calls=False,
    )
    feedback_convert_response = await chat_completion(
        request=request,
        provider=markdown_edit_request.request_type,
        client=markdown_edit_request.context
        if markdown_edit_request.request_type == "mcp"
        else markdown_edit_request.chat_completion_client,  # type: ignore
    )

    tool_calls = []
    word_comment_data = []
    if feedback_convert_response.choices[0].message.tool_calls:
        tool_calls = feedback_convert_response.choices[0].message.tool_calls
        tool_call = tool_calls[0].function
        if tool_call.name == FEEDBACK_TOOL_NAME:
            comments = tool_call.arguments.get("comments", [])
            for comment in comments:
                comment_data = WordCommentData(
                    comment_text=comment.get("comment_text", ""),
                    location_text=comment.get("location_text", ""),
                )
                comment_add_result = add_document_comment(doc, comment_data)
                # Sometimes comments fail to be added, in particular when there is MD formatting involved.
                if comment_add_result:
                    word_comment_data.append(comment_data)

    # Generate the summary string from the word_comment_data
    summary_parts = ["I have inserted the following comments:"]
    for comment in word_comment_data:
        summary_parts.append(f"Comment: {comment.comment_text}")
        summary_parts.append(f"Location: {comment.location_text}")
        summary_parts.append("")
    feedback_summary = "\n".join(summary_parts).strip()

    output = FeedbackOutput(
        feedback_summary=feedback_summary,
        word_comment_data=word_comment_data,
        reasoning=feedback_reasoning,
        tool_calls=tool_calls,
        llm_latency=feedback_convert_response.response_duration + feedback_response.response_duration,
    )
    return output

    # region
