import json
import logging
from enum import StrEnum
from textwrap import dedent
from typing import Annotated, Any, List, Optional

from attr import dataclass
from mcp import ClientSession, Tool
from pydantic import BaseModel, Field
from semantic_workbench_assistant.config import UISchema

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    name: str
    command: str
    args: List[str]
    env: Optional[dict[str, str]] = None
    prompt: Optional[str] = None


class MCPSession:
    name: str
    client_session: ClientSession
    tools: List[Tool] = []

    def __init__(self, name: str, client_session: ClientSession) -> None:
        self.name = name
        self.client_session = client_session

    async def initialize(self) -> None:
        # Load all tools from the session, later we can do the same for resources, prompts, etc.
        tools_result = await self.client_session.list_tools()
        self.tools = tools_result.tools
        logger.debug(f"Loaded {len(tools_result.tools)} tools from session '{self.name}'")


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "arguments": self.arguments,
        }

    def to_json(self, **kwargs) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, **kwargs)


class ToolMessageType(StrEnum):
    notice = "notice"
    tool_result = "tool_result"


@dataclass
class ToolCallResult:
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
    ] = True

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

    additional_instructions: Annotated[
        str,
        Field(
            title="Tools Instructions",
            description=dedent("""
                General instructions for using tools.  No need to include a list of tools or instruction
                on how to use them in general, that will be handled automatically.  Instead, use this
                space to provide any additional instructions for using specific tools, such folders to
                exclude in file searches, or instruction to always re-read a file before using it.
            """).strip(),
        ),
        UISchema(widget="textarea", enable_markdown_in_description=True),
    ] = dedent("""
        - When searching or browsing for files, consider the kinds of folders and files that should be avoided:
            - For example, for coding projects exclude folders like `.git`, `.vscode`, `node_modules`, and `dist`.
        - For each turn, always re-read a file before using it to ensure the most up-to-date information, especially
            when writing or editing files.
    """).strip()

    instructions_for_non_tool_models: Annotated[
        str,
        Field(
            title="Tools Instructions for Models Without Tools Support",
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

    file_system_paths: Annotated[
        list[str],
        Field(
            title="File System Paths",
            description="Paths to the file system for tools to use, relative to `/workspaces/` in the container.",
        ),
    ] = ["semanticworkbench"]
