import logging
from typing import Annotated, Any, Awaitable, Callable, List

from mcp import ClientSession, Tool
from mcp.client.session import SamplingFnT
from mcp.types import (
    CallToolRequestParams,
    CallToolResult,
)
from pydantic import BaseModel, Field
from semantic_workbench_assistant.config import UISchema

logger = logging.getLogger(__name__)


class MCPServerEnvConfig(BaseModel):
    key: Annotated[str, Field(title="Key", description="Environment variable key.")]
    value: Annotated[str, Field(title="Value", description="Environment variable value.")]


class MCPServerConfig(BaseModel):
    enabled: Annotated[bool, Field(title="Enabled", description="Enable the server.")] = True

    key: Annotated[str, Field(title="Key", description="Unique key for the server configuration.")]

    command: Annotated[
        str,
        Field(
            title="Command",
            description="Command to run the server, use url if using SSE transport.",
        ),
    ]

    args: Annotated[
        List[str],
        Field(title="Arguments", description="Arguments to pass to the server."),
    ] = []

    roots: Annotated[
        List[str],
        Field(
            title="Roots",
            description="Roots to pass to the server. Usually absolute URLs or absolute file paths.",
        ),
    ] = []

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


class HostedMCPServerConfig(MCPServerConfig):
    """
    For hosted MCP servers all fields except 'Enabled' are hidden. We only want users to toggle the 'Enabled' field.
    """

    enabled: Annotated[bool, Field(title="Enabled", description="Enable the server.")] = True

    key: Annotated[
        str,
        Field(title="Key", description="Unique key for the server configuration."),
        UISchema(readonly=True, widget="hidden"),
    ]

    command: Annotated[
        str,
        Field(
            title="Command",
            description="Command to run the server, use url if using SSE transport.",
        ),
        UISchema(readonly=True, widget="hidden"),
    ]

    args: Annotated[
        list[str],
        Field(title="Arguments", description="Arguments to pass to the server."),
        UISchema(readonly=True, widget="hidden"),
    ] = []

    roots: Annotated[
        list[str],
        Field(
            title="Roots",
            description="Roots to pass to the server. Usually absolute URLs or absolute file paths.",
        ),
        UISchema(readonly=True, widget="hidden"),
    ] = []

    env: Annotated[
        list[MCPServerEnvConfig],
        Field(title="Environment Variables", description="Environment variables to set."),
        UISchema(readonly=True, widget="hidden"),
    ] = []

    prompt: Annotated[
        str,
        Field(title="Prompt", description="Instructions for using the server."),
        UISchema(widget="textarea"),
        UISchema(readonly=True, widget="hidden"),
    ] = ""

    long_running: Annotated[
        bool,
        Field(title="Long Running", description="Does this server run long running tasks?"),
        UISchema(readonly=True, widget="hidden"),
    ] = False

    task_completion_estimate: Annotated[
        int,
        Field(
            title="Long Running Task Completion Time Estimate",
            description="Estimated time to complete an average long running task (in seconds).",
        ),
        UISchema(readonly=True, widget="hidden"),
    ] = 30


class MCPSession:
    config: MCPServerConfig
    client_session: ClientSession
    tools: List[Tool] = []
    is_connected: bool = True

    def __init__(self, config: MCPServerConfig, client_session: ClientSession) -> None:
        self.config = config
        self.client_session = client_session

    async def initialize(self) -> None:
        # Load all tools from the session, later we can do the same for resources, prompts, etc.
        tools_result = await self.client_session.list_tools()
        self.tools = tools_result.tools
        self.is_connected = True
        logger.debug(f"Loaded {len(tools_result.tools)} tools from session '{self.config.key}'")


class ExtendedCallToolRequestParams(CallToolRequestParams):
    id: str


class ExtendedCallToolResult(CallToolResult):
    id: str
    metadata: dict[str, Any]


# define types for callback functions
MCPErrorHandler = Callable[[MCPServerConfig, Exception], Any]
MCPLoggingMessageHandler = Callable[[str], Awaitable[None]]
MCPSamplingMessageHandler = SamplingFnT
