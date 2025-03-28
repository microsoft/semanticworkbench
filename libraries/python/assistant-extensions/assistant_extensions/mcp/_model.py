import logging
import os
from dataclasses import dataclass
from typing import Annotated, Any, Callable

from mcp.client.session import ListRootsFnT, LoggingFnT, MessageHandlerFnT, SamplingFnT
from mcp.types import (
    CallToolRequestParams,
    CallToolResult,
)
from mcp_extensions import ExtendedClientSession, ListResourcesFnT, ReadResourceFnT, WriteResourceFnT
from pydantic import BaseModel, Field
from semantic_workbench_assistant.config import UISchema

logger = logging.getLogger(__name__)


class MCPServerEnvConfig(BaseModel):
    key: Annotated[str, Field(title="Key", description="Environment variable key.")]
    value: Annotated[str, Field(title="Value", description="Environment variable value.")]


class MCPClientRoot(BaseModel):
    """
    Represents a root that can be passed to the MCP server.
    """

    name: Annotated[str, Field(title="Name", description="Name of the root.")] = ""
    uri: Annotated[str, Field(title="URI", description="URI or file-path of the root.")]


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
        list[str],
        Field(title="Arguments", description="Arguments to pass to the server."),
    ] = []

    roots: Annotated[
        list[MCPClientRoot],
        Field(
            title="Roots",
            description="Roots to pass to the server. Usually absolute URLs or absolute file paths.",
        ),
    ] = []

    env: Annotated[
        list[MCPServerEnvConfig],
        Field(title="Environment Variables", description="Environment variables to set."),
    ] = []

    prompt: Annotated[
        str,
        Field(title="Prompt", description="Instructions for using the server."),
        UISchema(widget="textarea"),
    ] = ""

    prompts_to_auto_include: Annotated[
        list[str],
        Field(
            title="Prompts to Automatically Include",
            description="Names of prompts provided by the MCP server that should be included in LLM completions.",
        ),
    ] = []

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
        list[MCPClientRoot],
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
        UISchema(readonly=True, widget="hidden"),
    ] = ""

    prompts_to_auto_include: Annotated[
        list[str],
        Field(
            title="Prompts to Automatically Include",
            description="Names of prompts provided by the MCP server that should be included in LLM completions.",
        ),
        UISchema(readonly=True, widget="hidden"),
    ] = []

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

    @staticmethod
    def from_env(
        key: str,
        url_env_var: str,
        enabled: bool = True,
        roots: list[MCPClientRoot] = [],
        prompts_to_auto_include: list[str] = [],
    ) -> "HostedMCPServerConfig":
        """Returns a HostedMCPServerConfig object with the command (URL) set from the environment variable."""
        env_value = os.getenv(url_env_var.upper()) or os.getenv(url_env_var.lower()) or ""

        enabled = enabled and bool(env_value)

        return HostedMCPServerConfig(
            key=key, command=env_value, enabled=enabled, roots=roots, prompts_to_auto_include=prompts_to_auto_include
        )


@dataclass
class MCPClientSettings:
    server_config: MCPServerConfig
    list_roots_callback: ListRootsFnT | None = None
    sampling_callback: SamplingFnT | None = None
    logging_callback: LoggingFnT | None = None
    message_handler: MessageHandlerFnT | None = None
    experimental_resource_callbacks: tuple[ListResourcesFnT, ReadResourceFnT, WriteResourceFnT] | None = None


class MCPSession:
    config: MCPClientSettings
    client_session: ExtendedClientSession
    # tools: List[Tool] = []
    is_connected: bool = True

    def __init__(self, config: MCPClientSettings, client_session: ExtendedClientSession) -> None:
        self.config = config
        self.client_session = client_session

    async def initialize(self) -> None:
        # Load all tools from the session, later we can do the same for resources, prompts, etc.
        tools_result = await self.client_session.list_tools()
        self.tools = tools_result.tools
        self.is_connected = True
        logger.debug(f"Loaded {len(tools_result.tools)} tools from session '{self.config.server_config.key}'")


class ExtendedCallToolRequestParams(CallToolRequestParams):
    id: str


class ExtendedCallToolResult(CallToolResult):
    id: str
    metadata: dict[str, Any]


# define types for callback functions
MCPErrorHandler = Callable[[MCPServerConfig, Exception], Any]
MCPSamplingMessageHandler = SamplingFnT
