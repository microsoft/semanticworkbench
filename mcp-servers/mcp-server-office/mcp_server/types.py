# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Callable, Literal

from mcp.server.fastmcp import Context
from mcp_extensions.llm.llm_types import MessageT, ToolCall
from pydantic import BaseModel, Field

from mcp_server.constants import COMMENT_AUTHOR, DEFAULT_DOC_EDIT_TASK

# region Feedback


class WordCommentData(BaseModel):
    id: str = Field(default="Unused")
    comment_text: str
    location_text: str
    date: str = Field(default="")
    author: str = Field(default=COMMENT_AUTHOR)
    occurrence: int = Field(default=1)


class FeedbackOutput(BaseModel):
    feedback_summary: str
    word_comment_data: list[WordCommentData] = Field(default_factory=list)
    reasoning: str
    tool_calls: list[ToolCall]
    llm_latency: float


class CommentAnalysisData(BaseModel):
    comment_data: WordCommentData
    output_message: str
    necessary_context_reasoning: str
    is_actionable: bool


class CommentAnalysisOutput(BaseModel):
    edit_instructions: str
    assistant_hints: str
    json_message: dict[str, Any]
    comment_analysis: list[CommentAnalysisData] = Field(default_factory=list)


# endregion


# region Evals


class CommentForEvals(BaseModel):
    location_text: str
    comment_text: str


class TestCase(BaseModel):
    test_case_name: str
    test_case_type: Literal["writing", "feedback", "comment_analysis"] = Field(default="writing")
    transcription_file: str
    open_document_markdown_file: str | None = Field(
        default=None, description="The txt or md file to load containing the document content."
    )
    next_ask: str
    attachments: list[str] = Field(default_factory=list)
    comments: list[CommentForEvals] = Field(default_factory=list)


# endregion


# region Markdown Edit


class CustomContext(BaseModel):
    chat_history: list[MessageT]
    document: str
    additional_context: str
    comments: list[WordCommentData] = Field(default_factory=list)


class MarkdownEditRequest(BaseModel):
    context: Context | CustomContext
    request_type: Literal["dev", "mcp"] = Field(default="mcp")
    chat_completion_client: Callable[..., Any] | None = Field(default=None)
    task: str = Field(default=DEFAULT_DOC_EDIT_TASK)
    additional_messages: list[MessageT] = Field(
        default_factory=list,
        description="Additional messages to add to the chat history. Useful for passing messages in multi-step routines.",
    )


class MarkdownEditOutput(BaseModel):
    change_summary: str
    output_message: str
    new_markdown: str
    reasoning: str
    tool_calls: list[ToolCall]
    llm_latency: float


# endregion
