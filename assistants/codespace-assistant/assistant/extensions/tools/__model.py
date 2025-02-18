import json
import logging
from enum import StrEnum
from textwrap import dedent
from typing import Annotated, Any, Callable, List

from attr import dataclass
from mcp import ClientSession, Tool
from pydantic import BaseModel, Field
from semantic_workbench_assistant.config import UISchema

logger = logging.getLogger(__name__)


# define type for on_logging_message callback
OnLoggingMessageHandler = Callable[[str], None]


class MCPServerEnvConfig(BaseModel):
    key: Annotated[str, Field(title="Key", description="Environment variable key.")]
    value: Annotated[str, Field(title="Value", description="Environment variable value.")]


class MCPServerConfig(BaseModel):
    enabled: Annotated[bool, Field(title="Enabled", description="Enable the server.")] = True

    key: Annotated[str, Field(title="Key", description="Unique key for the server configuration.")]

    command: Annotated[
        str, Field(title="Command", description="Command to run the server, use url if using SSE transport.")
    ]

    args: Annotated[List[str], Field(title="Arguments", description="Arguments to pass to the server.")]

    env: Annotated[
        List[MCPServerEnvConfig],
        Field(title="Environment Variables", description="Environment variables to set."),
    ] = []

    prompt: Annotated[
        str,
        Field(title="Prompt", description="Instructions for using the server."),
        UISchema(widget="textarea"),
    ] = ""

    long_running: Annotated[
        bool,
        Field(title="Long Running", description="Does this server run long running tasks?"),
    ] = False

    task_completion_estimate: Annotated[
        int,
        Field(
            title="Long Running Task Completion Time Estimate",
            description="Estimated time to complete an average long running task (in seconds).",
        ),
    ] = 30


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
        - Use the available tools to assist with specific tasks.
        - Before performing any file operations, use the `list_allowed_directories` tool to get a list of directories
            that are allowed for file operations. Always use paths relative to an allowed directory.
        - When searching or browsing for files, consider the kinds of folders and files that should be avoided:
            - For example, for coding projects exclude folders like `.git`, `.vscode`, `node_modules`, and `dist`.
        - For each turn, always re-read a file before using it to ensure the most up-to-date information, especially
            when writing or editing files.
        - The search tool does not appear to support wildcards, but does work with partial file names.
    """).strip()

    mcp_servers: Annotated[
        List[MCPServerConfig],
        Field(
            title="MCP Servers",
            description="Configuration for MCP servers that provide tools to the assistant.",
        ),
    ] = [
        MCPServerConfig(
            key="filesystem",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/workspaces/semanticworkbench"],
        ),
        MCPServerConfig(
            key="vscode",
            command="http://127.0.0.1:6010/sse",
            args=[],
            enabled=False,
        ),
        MCPServerConfig(
            key="bing-search",
            command="http://127.0.0.1:6030/sse",
            args=[],
            enabled=False,
        ),
        MCPServerConfig(
            key="open-deep-research",
            command="http://127.0.0.1:6020/sse",
            args=[],
            enabled=False,
        ),
        MCPServerConfig(
            key="giphy",
            command="http://http://127.0.0.1:6000/sse",
            args=[],
            enabled=False,
        ),
        MCPServerConfig(
            key="memory",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-memory"],
            prompt=dedent("""
                Follow these steps for each interaction:

                1. Memory Retrieval:
                - Always begin your chat by saying only "Remembering..." and retrieve all relevant information
                  from your knowledge graph
                - Always refer to your knowledge graph as your "memory"

                2. Memory
                - While conversing with the user, be attentive to any new information that falls into these categories:
                    a) Basic Identity (age, gender, location, job title, education level, etc.)
                    b) Behaviors (interests, habits, etc.)
                    c) Preferences (communication style, preferred language, etc.)
                    d) Goals (goals, targets, aspirations, etc.)
                    e) Relationships (personal and professional relationships up to 3 degrees of separation)

                3. Memory Update:
                - If any new information was gathered during the interaction, update your memory as follows:
                    a) Create entities for recurring organizations, people, and significant events
                    b) Connect them to the current entities using relations
                    b) Store facts about them as observations
            """).strip(),
            enabled=False,
        ),
        MCPServerConfig(
            key="sequential-thinking",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-sequential-thinking"],
            enabled=False,
        ),
    ]

    tools_disabled: Annotated[
        list[str],
        Field(
            title="Disabled Tools",
            description=dedent("""
                List of individual tools to disable. Use this if there is a problem tool that you do not want
                made visible to your assistant.
            """).strip(),
        ),
    ] = ["directory_tree"]


class MCPSession:
    config: MCPServerConfig
    client_session: ClientSession
    tools: List[Tool] = []

    def __init__(self, config: MCPServerConfig, client_session: ClientSession) -> None:
        self.config = config
        self.client_session = client_session

    async def initialize(self) -> None:
        # Load all tools from the session, later we can do the same for resources, prompts, etc.
        tools_result = await self.client_session.list_tools()
        self.tools = tools_result.tools
        logger.debug(f"Loaded {len(tools_result.tools)} tools from session '{self.config.key}'")


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
