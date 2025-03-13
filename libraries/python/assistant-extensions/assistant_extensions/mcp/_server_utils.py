import logging
import pathlib
from asyncio import CancelledError
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Any, AsyncIterator, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import pydantic
from mcp import ClientSession, types
from mcp.client.session import SamplingFnT
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.shared.context import RequestContext

from . import _devtunnel

from ._model import (
    MCPSamplingMessageHandler,
    MCPServerConfig,
    MCPSession,
    MCPToolsConfigModel,
)

logger = logging.getLogger(__name__)


def get_env_dict(server_config: MCPServerConfig) -> dict[str, str] | None:
    """Get the environment variables as a dictionary."""
    env_dict = {env.key: env.value for env in server_config.env}
    if len(env_dict) == 0:
        return None
    return env_dict


@asynccontextmanager
async def connect_to_mcp_server(
    server_config: MCPServerConfig,
    sampling_callback: Optional[SamplingFnT] = None,
) -> AsyncIterator[ClientSession]:
    """Connect to a single MCP server defined in the config."""
    transport = "sse" if server_config.command.startswith("http") else "stdio"

    match transport:
        case "sse":
            async with connect_to_mcp_server_sse(
                server_config, sampling_callback
            ) as client_session:
                yield client_session

        case "stdio":
            async with connect_to_mcp_server_stdio(
                server_config, sampling_callback
            ) as client_session:
                yield client_session


def list_roots_callback_for(server_config: MCPServerConfig):
    """
    Provides a callback to return the list of "roots" for a given server config.
    """

    def root_to_uri(root: str) -> pydantic.AnyUrl | pydantic.FileUrl:
        # if the root is a URL, return it as is
        if "://" in root:
            return pydantic.AnyUrl(root)

        # otherwise, assume it is a file path, and convert to a file URL
        path = pathlib.Path(root)
        match path:
            case pathlib.WindowsPath():
                return pydantic.FileUrl(f"file:///{path.as_posix()}")
            case _:
                return pydantic.FileUrl(f"file://{path.as_posix()}")

    async def cb(
        context: RequestContext[ClientSession, Any],
    ) -> types.ListRootsResult | types.ErrorData:
        roots = server_config.roots
        return types.ListRootsResult(
            roots=[
                # mcp sdk is currently typed to FileUrl, but the MCP spec allows for any URL
                # the mcp sdk doesn't call any of the FileUrl methods, so this is safe for now
                types.Root(uri=root_to_uri(root))  # type: ignore
                for root in roots
            ]
        )

    return cb


@asynccontextmanager
async def connect_to_mcp_server_stdio(
    server_config: MCPServerConfig,
    sampling_callback: Optional[SamplingFnT] = None,
) -> AsyncIterator[ClientSession]:
    """Connect to a single MCP server defined in the config."""

    server_params = StdioServerParameters(
        command=server_config.command,
        args=server_config.args,
        env=get_env_dict(server_config),
    )
    logger.debug(
        f"Attempting to connect to {server_config.key} with command: {server_config.command} {' '.join(server_config.args)}"
    )
    try:
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(
                read_stream,
                write_stream,
                list_roots_callback=list_roots_callback_for(server_config),
                sampling_callback=sampling_callback,
            ) as client_session:
                await client_session.initialize()
                yield client_session  # Yield the session for use

    except Exception as e:
        logger.exception(f"Error connecting to {server_config.key}: {e}")
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
async def connect_to_mcp_server_sse(
    server_config: MCPServerConfig,
    sampling_callback: Optional[SamplingFnT] = None,
) -> AsyncIterator[ClientSession]:
    """Connect to a single MCP server defined in the config using SSE transport."""

    try:
        headers = get_env_dict(server_config)
        url = server_config.command

        devtunnel_config = _devtunnel.config_from(server_config.args)
        if devtunnel_config:
            url = await _devtunnel.forwarded_url_for(
                original_url=url, devtunnel=devtunnel_config
            )

        logger.debug(
            f"Attempting to connect to {server_config.key} with SSE transport: {url}"
        )

        # FIXME: Bumping sse_read_timeout to 15 minutes and timeout to 5 minutes, but this should be configurable
        async with sse_client(
            url=url, headers=headers, timeout=60 * 5, sse_read_timeout=60 * 15
        ) as (
            read_stream,
            write_stream,
        ):
            async with ClientSession(
                read_stream,
                write_stream,
                list_roots_callback=list_roots_callback_for(server_config),
                sampling_callback=sampling_callback,
            ) as client_session:
                await client_session.initialize()
                yield client_session  # Yield the session for use

    except ExceptionGroup as e:
        logger.exception(f"TaskGroup failed in SSE client for {server_config.key}: {e}")
        for sub in e.exceptions:
            logger.error(f"Sub-exception: {server_config.key}: {sub}")
        # If there's exactly one underlying exception, re-raise it
        if len(e.exceptions) == 1:
            raise e.exceptions[0]
        else:
            raise
    except CancelledError as e:
        logger.exception(
            f"Task was cancelled in SSE client for {server_config.key}: {e}"
        )
        raise
    except RuntimeError as e:
        logger.exception(f"Runtime error in SSE client for {server_config.key}: {e}")
        raise
    except Exception as e:
        logger.exception(f"Error connecting to {server_config.key}: {e}")
        raise


async def refresh_mcp_sessions(mcp_sessions: list[MCPSession]) -> list[MCPSession]:
    """
    Check each MCP session for connectivity. If a session is marked as disconnected,
    attempt to reconnect it using reconnect_mcp_session.
    """
    active_sessions = []
    for session in mcp_sessions:
        if not session.is_connected:
            logger.info(
                f"Session {session.config.key} is disconnected. Attempting to reconnect..."
            )
            new_session = await reconnect_mcp_session(session.config)
            if new_session:
                active_sessions.append(new_session)
            else:
                logger.error(f"Failed to reconnect MCP server {session.config.key}.")
        else:
            active_sessions.append(session)
    return active_sessions


async def reconnect_mcp_session(server_config: MCPServerConfig) -> MCPSession | None:
    """
    Attempt to reconnect to the MCP server using the provided configuration.
    Returns a new MCPSession if successful, or None otherwise.
    This version relies directly on the existing connection context manager
    to avoid interfering with cancel scopes.
    """
    try:
        async with connect_to_mcp_server(server_config) as client_session:
            if client_session is None:
                logger.error(
                    f"Reconnection returned no client session for {server_config.key}"
                )
                return None

            new_session = MCPSession(
                config=server_config, client_session=client_session
            )
            await new_session.initialize()
            new_session.is_connected = True
            logger.info(f"Successfully reconnected to MCP server {server_config.key}")
            return new_session
    except Exception as e:
        logger.exception(f"Error reconnecting MCP server {server_config.key}: {e}")
        return None


class MCPServerConnectionError(Exception):
    """Custom exception for errors related to MCP server connections."""

    def __init__(self, server_config: MCPServerConfig, error: Exception):
        super().__init__(str(error))
        self.server_config = server_config
        self.error = error


async def establish_mcp_sessions(
    mcp_server_configs: list[MCPServerConfig],
    stack: AsyncExitStack,
    sampling_handler: Optional[MCPSamplingMessageHandler] = None,
) -> list[MCPSession]:
    """
    Establish connections to multiple MCP servers and return their sessions.
    """

    mcp_sessions: list[MCPSession] = []
    for server_config in mcp_server_configs:
        if not server_config.enabled:
            logger.debug("skipping disabled MCP server: %s", server_config.key)
            continue

        try:
            client_session: ClientSession = await stack.enter_async_context(
                connect_to_mcp_server(
                    server_config,
                    sampling_callback=sampling_handler,
                )
            )
        except Exception as e:
            # Log a cleaner error message for this specific server
            logger.exception("failed to connect to MCP server: %s", server_config.key)
            raise MCPServerConnectionError(server_config, e) from e

        mcp_session = MCPSession(
            config=server_config, client_session=client_session
        )
        await mcp_session.initialize()
        mcp_sessions.append(mcp_session)

    return mcp_sessions


def get_enabled_mcp_server_configs(tools: MCPToolsConfigModel) -> list[MCPServerConfig]:
    if not tools.enabled:
        return []

    return [
        server_config
        for server_config in tools.mcp_servers
        if server_config.enabled
    ]


def get_mcp_server_prompts(mcp_servers: list[MCPServerConfig]) -> list[str]:
    """Get the prompts for all MCP servers that have them."""
    return [
        mcp_server.prompt
        for mcp_server in mcp_servers
        if mcp_server.prompt
    ]
