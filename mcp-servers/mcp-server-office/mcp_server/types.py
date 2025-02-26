# Copyright (c) Microsoft. All rights reserved.

from enum import Enum
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel


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
