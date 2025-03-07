# Copyright (c) Microsoft. All rights reserved.

from enum import Enum
from typing import Any, Callable, Generic, Literal, TypeVar

from mcp.server.fastmcp import Context
from pydantic import BaseModel, Field

from mcp_server.constants import COMMENT_AUTHOR, DEFAULT_DOC_EDIT_TASK

# region Chat Completion


class Role(str, Enum):
    ASSISTANT = "assistant"
    DEVELOPER = "developer"
    SYSTEM = "system"
    TOOL = "tool"
    USER = "user"


class ContentPartType(str, Enum):
    TEXT = "text"
    IMAGE = "image_url"


class TextContent(BaseModel):
    type: Literal[ContentPartType.TEXT] = ContentPartType.TEXT
    text: str


class ImageDetail(str, Enum):
    AUTO = "auto"
    LOW = "low"
    HIGH = "high"


class ImageUrl(BaseModel):
    url: str
    detail: ImageDetail = ImageDetail.AUTO


class ImageContent(BaseModel):
    type: Literal[ContentPartType.IMAGE] = ContentPartType.IMAGE
    image_url: ImageUrl


ContentT = TypeVar("ContentT", bound=str | list[TextContent | ImageContent])
RoleT = TypeVar("RoleT", bound=Role)


class BaseMessage(BaseModel, Generic[ContentT, RoleT]):
    content: ContentT
    role: RoleT
    name: str | None = None


class Function(BaseModel):
    name: str
    arguments: dict[str, Any]


class PartialFunction(BaseModel):
    name: str
    arguments: str | dict[str, Any]


class ToolCall(BaseModel):
    id: str
    function: Function
    type: Literal["function"] = "function"


class PartialToolCall(BaseModel):
    id: str | None
    function: PartialFunction
    type: Literal["function"] = "function"


class DeveloperMessage(BaseMessage[str, Literal[Role.DEVELOPER]]):
    role: Literal[Role.DEVELOPER] = Role.DEVELOPER


class SystemMessage(BaseMessage[str, Literal[Role.SYSTEM]]):
    role: Literal[Role.SYSTEM] = Role.SYSTEM


class UserMessage(BaseMessage[str | list[TextContent | ImageContent], Literal[Role.USER]]):
    role: Literal[Role.USER] = Role.USER


class AssistantMessage(BaseMessage[str, Literal[Role.ASSISTANT]]):
    role: Literal[Role.ASSISTANT] = Role.ASSISTANT
    refusal: str | None = None
    tool_calls: list[ToolCall] | None = None


class ToolMessage(BaseMessage[str, Literal[Role.TOOL]]):
    # A tool message's name field will be interpreted as "tool_call_id"
    role: Literal[Role.TOOL] = Role.TOOL


MessageT = AssistantMessage | DeveloperMessage | SystemMessage | ToolMessage | UserMessage


class ChatCompletionRequest(BaseModel):
    messages: list[MessageT]
    model: str
    stream: bool = Field(default=False)

    max_completion_tokens: int | None = Field(default=None)
    context_window: int | None = Field(default=None)
    logprobs: bool | None = Field(default=None)
    n: int | None = Field(default=None)

    tools: list[dict[str, Any]] | None = Field(default=None)
    tool_choice: str | None = Field(default=None)
    parallel_tool_calls: bool | None = Field(default=None)
    json_mode: bool | None = Field(default=None)
    structured_outputs: dict[str, Any] | None = Field(default=None)

    temperature: float | None = Field(default=None)
    reasoning_effort: Literal["low", "medium", "high"] | None = Field(default=None)
    top_p: float | None = Field(default=None)
    logit_bias: dict[str, float] | None = Field(default=None)
    top_logprobs: int | None = Field(default=None)
    frequency_penalty: float | None = Field(default=None)
    presence_penalty: float | None = Field(default=None)
    stop: str | list[str] | None = Field(default=None)

    seed: int | None = Field(default=None)

    max_tokens: int | None = Field(
        default=None,
        description="Sometimes `max_completion_tokens` is not correctly supported so we provide this as a fallback.",
    )


class ChatCompletionChoice(BaseModel):
    message: AssistantMessage
    finish_reason: Literal["stop", "length", "tool_calls", "content_filter"]

    json_message: dict[str, Any] | None = Field(default=None)
    logprobs: list[dict[str, Any] | list[dict[str, Any]]] | None = Field(default=None)

    extras: Any | None = Field(default=None)


class ChatCompletionResponse(BaseModel):
    choices: list[ChatCompletionChoice]

    errors: str = Field(default="")

    completion_tokens: int
    prompt_tokens: int
    completion_detailed_tokens: dict[str, int] | None = Field(default=None)
    prompt_detailed_tokens: dict[str, int] | None = Field(default=None)
    response_duration: float

    system_fingerprint: str | None = Field(default=None)

    extras: Any | None = Field(default=None)


# endregion


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
