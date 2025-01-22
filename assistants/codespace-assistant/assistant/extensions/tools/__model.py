from enum import StrEnum
import json
from textwrap import dedent
from typing import Annotated, Any, List, Optional

from attr import dataclass
from pydantic import BaseModel, Field
from semantic_workbench_assistant.config import UISchema


@dataclass
class MCPServerConfig:
    name: str
    command: str
    args: List[str]
    env: Optional[dict[str, str]] = None


@dataclass
class ToolAction:
    id: str
    name: str
    arguments: dict[str, Any]

    def to_json(self, **kwargs) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, **kwargs)


class ToolMessageType(StrEnum):
    notice = "notice"
    tool_result = "tool_result"

@dataclass
class ToolActionResult:
    id: str
    content: str
    message_type: ToolMessageType
    metadata: dict[str, Any]


class ToolsConfigModel(BaseModel):
    enabled: Annotated[
        bool,
        Field(
            title="Enabled",
            description="Enable experimental use of tools.",
        ),
    ] = False

    max_steps: Annotated[
        int,
        Field(
            title="Maximum Steps",
            description="The maximum number of steps to take when using tools, to avoid infinite loops.",
        ),
    ] = 5

    max_steps_truncation_message: Annotated[
        str,
        Field(
            title="Maximum Steps Truncation Message",
            description="The message to display when the maximum number of steps is reached.",
        ),
    ] = "[ Maximum steps reached for this turn, engage with assistant to continue ]"

    tools_instructions: Annotated[
        str,
        Field(
            title="Tools Instructions",
            description=dedent("""
                Some models don't support tools (like OpenAI reasoning models), so these instructions
                are only used to implement tool support through custom instruction and injection of
                the tool definitions.  Make sure to include {{tools}} in the instructions.
            """),
        ),
        UISchema(widget="textarea", enable_markdown_in_description=True),
    ] = dedent("""
        You can perform specific tasks using available tools. When you need to use a tool, respond
        with a strict JSON object containing only the tool's `id` and function name and arguments.

        Available Tools:
        {{tools}}

        ### Instructions:
        - If you need to use a tool to answer the user's query, respond with **ONLY** a JSON object.
        - If you can answer without using a tool, provide the answer directly.
        - **No code, no text, no markdown** within the JSON.
        - Ensure that all values are plain data types (e.g., strings, numbers).
        - **Do not** include any additional characters, functions, or expressions within the JSON.
    """).strip()
