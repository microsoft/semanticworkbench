import logging
from asyncio import CancelledError
from contextlib import AsyncExitStack, asynccontextmanager
from typing import AsyncIterator, Callable, List, Optional, TypeVar, Type
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters, stdio_client
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from ._model import KeyValueConfigBase, MCPServerConfig, MCPSession, MCPToolsConfigModel

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=KeyValueConfigBase)


def get_key_value_dict(items: List[T]) -> dict[str, str] | None:
    """
    Get a dictionary of key-value pairs from a list of KeyValueConfigBase objects.
    
    Args:
        items: List of KeyValueConfigBase objects
        
    Returns:
        A dictionary of key-value pairs, or None if the list is empty
    """
    key_value_dict = {item.key: item.value for item in items}
    if len(key_value_dict) == 0:
        return None
    return key_value_dict


def get_env_dict(server_config: MCPServerConfig) -> dict[str, str] | None:
    """Get the environment variables as a dictionary."""
    return get_key_value_dict(server_config.env)


def get_args_list(server_config: MCPServerConfig) -> List[str]:
    """
    Convert the structured args to a flat list for stdio transport.
    For backwards compatibility with libraries expecting a flat list.
    """
    args_list = []
    for arg in server_config.args:
        args_list.append(arg.key)
        if arg.value:  # Only add the value if it's non-empty
            args_list.append(arg.value)
    return args_list


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
    """Connect to a single MCP server defined in the config using stdio transport."""
    # Convert the structured args to a flat list
    args_list = get_args_list(server_config)
    
    server_params = StdioServerParameters(
        command=server_config.command,
        args=args_list,
        env=get_env_dict(server_config),
    )
    logger.debug(
        f"Attempting to connect to {server_config.key} with command: {server_config.command} {' '.join(args_list)}"
    )
    try:
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as client_session:
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
) -> AsyncIterator[Optional[ClientSession]]:
    """Connect to a single MCP server defined in the config using SSE transport."""

    try:
        headers = get_env_dict(server_config)
        url = server_config.command
        url_params = {}
        
        # Process args to extract query parameters
        if server_config.args:
            # Create args dictionary
            args_dict = get_key_value_dict(server_config.args)
            if args_dict:
                # Add all arg parameters to URL
                url_params.update(args_dict)
                logger.debug(f"Added URL parameters from args: {args_dict}")
        
        # Add parameters to URL
        if url_params:
            url = add_params_to_url(url, url_params)
            logger.debug(f"Final URL with parameters: {url}")

        logger.debug(f"Connecting to {server_config.key} with SSE transport: {url}")

        # FIXME: Bumping sse_read_timeout to 15 minutes and timeout to 5 minutes, but this should be configurable
        async with sse_client(
            url=url, headers=headers, timeout=60 * 5, sse_read_timeout=60 * 15
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
