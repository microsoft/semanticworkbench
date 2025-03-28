import logging
import pathlib
from asyncio import CancelledError
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Any, AsyncIterator
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import pydantic
from mcp import ClientSession, McpError, types
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.shared.context import RequestContext
from mcp_extensions import ExtendedClientSession
from semantic_workbench_assistant.assistant_app import ConversationContext

from . import _devtunnel
from ._model import (
    MCPClientSettings,
    MCPServerConfig,
    MCPSession,
)

logger = logging.getLogger(__name__)


def get_env_dict(server_config: MCPServerConfig) -> dict[str, str] | None:
    """Get the environment variables as a dictionary."""
    env_dict = {env.key: env.value for env in server_config.env}
    if len(env_dict) == 0:
        return None
    return env_dict


@asynccontextmanager
async def connect_to_mcp_server(client_settings: MCPClientSettings) -> AsyncIterator[ExtendedClientSession]:
    """Connect to a single MCP server defined in the config."""
    transport = "sse" if client_settings.server_config.command.startswith("http") else "stdio"

    match transport:
        case "sse":
            async with connect_to_mcp_server_sse(client_settings) as client_session:
                yield client_session

        case "stdio":
            async with connect_to_mcp_server_stdio(client_settings) as client_session:
                yield client_session


def list_roots_callback_for(context: ConversationContext, server_config: MCPServerConfig):
    """
    Provides a callback to return the list of "roots" for a given server config.
    """

    def root_to_pydantic_url(root_uri: str) -> pydantic.AnyUrl | pydantic.FileUrl:
        root_uri = root_uri.replace("{assistant_id}", context.assistant.id)
        root_uri = root_uri.replace("{conversation_id}", context.id)

        # if the root is a URL, return it as is
        if "://" in root_uri:
            return pydantic.AnyUrl(root_uri)

        # otherwise, assume it is a file path, and convert to a file URL
        path = pathlib.Path(root_uri)
        match path:
            case pathlib.WindowsPath():
                return pydantic.FileUrl(f"file:///{path.as_posix()}")
            case _:
                return pydantic.FileUrl(f"file://{path.as_posix()}")

    async def cb(
        context: RequestContext[ClientSession, Any],
    ) -> types.ListRootsResult | types.ErrorData:
        try:
            roots = [
                # mcp sdk is currently typed to FileUrl, but the MCP spec allows for any URL
                # the mcp sdk doesn't call any of the FileUrl methods, so this is safe for now
                types.Root(name=root.name or None, uri=root_to_pydantic_url(root.uri))  # type: ignore
                for root in server_config.roots
            ]
        except Exception as e:
            logger.exception("error returning roots for %s", server_config.key)
            return types.ErrorData(
                code=500,
                message=f"Error returning roots: {e}",
            )

        return types.ListRootsResult(roots=roots)

    return cb


@asynccontextmanager
async def connect_to_mcp_server_stdio(client_settings: MCPClientSettings) -> AsyncIterator[ExtendedClientSession]:
    """Connect to a single MCP server defined in the config."""

    server_params = StdioServerParameters(
        command=client_settings.server_config.command,
        args=client_settings.server_config.args,
        env=get_env_dict(client_settings.server_config),
    )
    logger.debug(
        f"Attempting to connect to {client_settings.server_config.key} with command: {client_settings.server_config.command} {' '.join(client_settings.server_config.args)}"
    )
    try:
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ExtendedClientSession(
                read_stream,
                write_stream,
                list_roots_callback=client_settings.list_roots_callback,
                sampling_callback=client_settings.sampling_callback,
                message_handler=client_settings.message_handler,
                logging_callback=client_settings.logging_callback,
                experimental_resource_callbacks=client_settings.experimental_resource_callbacks,
            ) as client_session:
                await client_session.initialize()
                yield client_session  # Yield the session for use

    except Exception as e:
        logger.exception(f"Error connecting to {client_settings.server_config.key}: {e}")
        raise


def add_params_to_url(url: str, params: dict[str, str]) -> str:
    """Add parameters to a URL."""
    parsed_url = urlparse(url)
    query_params = dict()
    if parsed_url.query:
        for key, value_list in parse_qs(parsed_url.query).items():
            if value_list:
                query_params[key] = value_list[0]
    query_params.update(params)
    url_parts = list(parsed_url)
    url_parts[4] = urlencode(query_params)  # 4 is the query part
    return urlunparse(url_parts)


@asynccontextmanager
async def connect_to_mcp_server_sse(client_settings: MCPClientSettings) -> AsyncIterator[ExtendedClientSession]:
    """Connect to a single MCP server defined in the config using SSE transport."""

    try:
        headers = get_env_dict(client_settings.server_config)
        url = client_settings.server_config.command

        devtunnel_config = _devtunnel.config_from(client_settings.server_config.args)
        if devtunnel_config:
            url = await _devtunnel.forwarded_url_for(original_url=url, devtunnel=devtunnel_config)

        logger.debug(f"Attempting to connect to {client_settings.server_config.key} with SSE transport: {url}")

        # FIXME: Bumping sse_read_timeout to 15 minutes and timeout to 5 minutes, but this should be configurable
        async with sse_client(url=url, headers=headers, timeout=60 * 5, sse_read_timeout=60 * 15) as (
            read_stream,
            write_stream,
        ):
            async with ExtendedClientSession(
                read_stream,
                write_stream,
                list_roots_callback=client_settings.list_roots_callback,
                sampling_callback=client_settings.sampling_callback,
                message_handler=client_settings.message_handler,
                experimental_resource_callbacks=client_settings.experimental_resource_callbacks,
            ) as client_session:
                await client_session.initialize()
                yield client_session  # Yield the session for use

    except ExceptionGroup as e:
        logger.exception(f"TaskGroup failed in SSE client for {client_settings.server_config.key}: {e}")
        for sub in e.exceptions:
            logger.error(f"Sub-exception: {client_settings.server_config.key}: {sub}")
        # If there's exactly one underlying exception, re-raise it
        if len(e.exceptions) == 1:
            raise e.exceptions[0]
        else:
            raise
    except CancelledError as e:
        logger.exception(f"Task was cancelled in SSE client for {client_settings.server_config.key}: {e}")
        raise
    except RuntimeError as e:
        logger.exception(f"Runtime error in SSE client for {client_settings.server_config.key}: {e}")
        raise
    except Exception as e:
        logger.exception(f"Error connecting to {client_settings.server_config.key}: {e}")
        raise


async def refresh_mcp_sessions(
    mcp_sessions: list[MCPSession],
) -> list[MCPSession]:
    """
    Check each MCP session for connectivity. If a session is marked as disconnected,
    attempt to reconnect it using reconnect_mcp_session.
    """
    active_sessions = []
    for session in mcp_sessions:
        if not session.is_connected:
            logger.info(f"Session {session.config.server_config.key} is disconnected. Attempting to reconnect...")
            new_session = await reconnect_mcp_session(session.config)
            if new_session:
                active_sessions.append(new_session)
            else:
                logger.error(f"Failed to reconnect MCP server {session.config.server_config.key}.")
        else:
            active_sessions.append(session)
    return active_sessions


async def reconnect_mcp_session(client_settings: MCPClientSettings) -> MCPSession | None:
    """
    Attempt to reconnect to the MCP server using the provided configuration.
    Returns a new MCPSession if successful, or None otherwise.
    This version relies directly on the existing connection context manager
    to avoid interfering with cancel scopes.
    """
    try:
        async with connect_to_mcp_server(client_settings) as client_session:
            if client_session is None:
                logger.error("Reconnection returned no client session for %s", client_settings.server_config.key)
                return None

            new_session = MCPSession(config=client_settings, client_session=client_session)
            await new_session.initialize()
            new_session.is_connected = True
            logger.info("Successfully reconnected to MCP server %s", client_settings.server_config.key)
            return new_session
    except Exception:
        logger.exception("Error reconnecting MCP server %s", client_settings.server_config.key)
        return None


class MCPServerConnectionError(Exception):
    """Custom exception for errors related to MCP server connections."""

    def __init__(self, server_config: MCPServerConfig, error: Exception):
        super().__init__(str(error))
        self.server_config = server_config
        self.error = error


async def establish_mcp_sessions(
    client_settings: list[MCPClientSettings],
    stack: AsyncExitStack,
) -> list[MCPSession]:
    """
    Establish connections to multiple MCP servers and return their sessions.
    """

    mcp_sessions: list[MCPSession] = []
    for client_config in client_settings:
        if not client_config.server_config.enabled:
            logger.debug("skipping disabled MCP server: %s", client_config.server_config.key)
            continue

        try:
            client_session: ExtendedClientSession = await stack.enter_async_context(
                connect_to_mcp_server(client_config)
            )
        except Exception as e:
            # Log a cleaner error message for this specific server
            logger.exception("failed to connect to MCP server: %s", client_config.server_config.key)
            raise MCPServerConnectionError(client_config.server_config, e) from e

        mcp_session = MCPSession(config=client_config, client_session=client_session)
        await mcp_session.initialize()
        mcp_sessions.append(mcp_session)

    return mcp_sessions


def get_enabled_mcp_server_configs(mcp_servers: list[MCPServerConfig]) -> list[MCPServerConfig]:
    return [server_config for server_config in mcp_servers if server_config.enabled]


async def get_mcp_server_prompts(mcp_sessions: list[MCPSession]) -> list[str]:
    """Get the prompts for all MCP servers that have them."""
    prompts = [session.config.server_config.prompt for session in mcp_sessions if session.config.server_config.prompt]

    for session in mcp_sessions:
        for prompt_name in session.config.server_config.prompts_to_auto_include:
            try:
                prompt_result = await session.client_session.get_prompt(prompt_name)
                for message in prompt_result.messages:
                    if isinstance(message.content, types.TextContent):
                        prompts.append(message.content.text)
                        continue

                    logger.warning(
                        f"Unexpected message content type in memory prompt '{prompt_name}': {type(message.content)}"
                    )
            except McpError:
                logger.exception(
                    "Failed to retrieve prompt '%s' from MCP server %s", prompt_name, session.config.server_config.key
                )

    return prompts
