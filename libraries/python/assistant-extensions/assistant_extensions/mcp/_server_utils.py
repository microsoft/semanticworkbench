import logging
from asyncio import CancelledError
from contextlib import AsyncExitStack, asynccontextmanager
from typing import AsyncIterator, Callable, List, Optional
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters, stdio_client

from ._model import MCPServerConfig, MCPSession, MCPToolsConfigModel

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
) -> AsyncIterator[Optional[ClientSession]]:
    """Connect to a single MCP server defined in the config."""
    if server_config.command.startswith("http"):
        async with connect_to_mcp_server_sse(server_config) as client_session:
            yield client_session
    else:
        async with connect_to_mcp_server_stdio(server_config) as client_session:
            yield client_session


@asynccontextmanager
async def connect_to_mcp_server_stdio(
    server_config: MCPServerConfig,
) -> AsyncIterator[Optional[ClientSession]]:
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
            async with ClientSession(read_stream, write_stream) as client_session:
                await client_session.initialize()
                yield client_session  # Yield the session for use

    except Exception as e:
        logger.exception(f"Error connecting to {server_config.key}: {e}")
        raise


@asynccontextmanager
async def connect_to_mcp_server_sse(
    server_config: MCPServerConfig,
) -> AsyncIterator[Optional[ClientSession]]:
    """Connect to a single MCP server defined in the config using SSE transport."""

    try:
        logger.debug(
            f"Attempting to connect to {server_config.key} with SSE transport: {server_config.command}"
        )
        headers = get_env_dict(server_config)

        # FIXME: Bumping sse_read_timeout to 15 minutes and timeout to 5 minutes, but this should be configurable
        async with sse_client(
            url=server_config.command, headers=headers, timeout=60 * 5, sse_read_timeout=60 * 15
        ) as (
            read_stream,
            write_stream,
        ):
            async with ClientSession(read_stream, write_stream) as client_session:
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
            logger.info(f"Session {session.config.key} is disconnected. Attempting to reconnect...")
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
                logger.error(f"Reconnection returned no client session for {server_config.key}")
                return None

            new_session = MCPSession(config=server_config, client_session=client_session)
            await new_session.initialize()
            new_session.is_connected = True
            logger.info(f"Successfully reconnected to MCP server {server_config.key}")
            return new_session
    except Exception as e:
        logger.exception(f"Error reconnecting MCP server {server_config.key}: {e}")
        return None


async def establish_mcp_sessions(
    tools_config: MCPToolsConfigModel, stack: AsyncExitStack, error_handler: Optional[Callable] = None
) -> List[MCPSession]:
    mcp_sessions: List[MCPSession] = []
    for server_config in tools_config.mcp_servers:
        if not server_config.enabled:
            logger.debug(f"Skipping disabled server: {server_config.key}")
            continue
        try:
            client_session: ClientSession | None = await stack.enter_async_context(
                connect_to_mcp_server(server_config)
            )
        except Exception as e:
            # Log a cleaner error message for this specific server
            logger.error(f"Failed to connect to MCP server {server_config.key}: {e}")
            # Also notify the user about this server failure here.
            if error_handler:
                await error_handler(server_config, e)
            # Abort the connection attempt for the servers to avoid only partial server connections
            # This could lead to assistant creatively trying to use the other tools to compensate
            # for the missing tools, which can sometimes be very problematic.
            return []

        if client_session:
            mcp_session = MCPSession(config=server_config, client_session=client_session)
            await mcp_session.initialize()
            mcp_sessions.append(mcp_session)
        else:
            logger.warning(f"Could not establish session with {server_config.key}")
    return mcp_sessions


def get_mcp_server_prompts(tools_config: MCPToolsConfigModel) -> List[str]:
    """Get the prompts for all MCP servers."""
    return [
        mcp_server.prompt
        for mcp_server in tools_config.mcp_servers
        if mcp_server.prompt
    ]
