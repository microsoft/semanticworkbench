# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Callable, Literal

from mcp.server.fastmcp import Context
from mcp_extensions.llm.llm_types import MessageT, ToolCall
from pydantic import BaseModel, Field


class CustomContext(BaseModel):
    chat_history: list[MessageT]
    document: str
    file_type: Literal["markdown", "latex"] = Field(default="markdown")
    additional_context: str


class FileOpRequest(BaseModel):
    context: Context | CustomContext
    request_type: Literal["dev", "mcp"] = Field(default="mcp")
    chat_completion_client: Callable[..., Any] | None = Field(default=None)
    file_type: Literal["markdown", "latex"] = Field(default="markdown")
    file_content: str = Field(default="")
    task: str = Field(default="")


class EditOutput(BaseModel):
    change_summary: str
    output_message: str
    new_content: str
    reasoning: str
    tool_calls: list[ToolCall]
    llm_latency: float


class CommentOutput(BaseModel):
    new_content: str
    comment_instructions: str
    reasoning: str
    tool_calls: list[ToolCall]
    llm_latency: float


class Block(BaseModel):
    id: int
    content: str


class EditOperation(BaseModel):
    type: str


class InsertOperation(EditOperation):
    type: str = "insert"
    index: int
    content: str


class UpdateOperation(EditOperation):
    type: str = "update"
    index: int
    content: str


class RemoveOperation(EditOperation):
    type: str = "remove"
    start_index: int
    end_index: int


class TestCase(BaseModel):
    test_case_name: str
    test_case_type: Literal["writing", "comments"] = Field(default="writing")
    file_type: Literal["markdown", "latex"] = Field(default="markdown")
    transcription_file: str
    open_file: str | None = Field(
        default=None, description="The txt or md file to load containing the document content."
    )
    next_ask: str
    attachments: list[str] = Field(default_factory=list)


class FileOpTelemetry(BaseModel):
    reasoning_latency: float = Field(default=0.0, description="Time spent on reasoning LLM call in seconds")
    convert_latency: float = Field(default=0.0, description="Time spent on convert LLM call in seconds")
    change_summary_latency: float = Field(default=0.0, description="Time spent on change summary LLM call in seconds")
    total_latency: float = Field(default=0.0, description="Total LLM latency in seconds")

    def reset(self) -> None:
        self.reasoning_latency = 0.0
        self.convert_latency = 0.0
        self.change_summary_latency = 0.0
        self.total_latency = 0.0
