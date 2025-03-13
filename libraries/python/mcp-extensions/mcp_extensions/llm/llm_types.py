from enum import Enum
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, Field


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
