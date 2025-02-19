import logging
from asyncio import CancelledError
from contextlib import AsyncExitStack, asynccontextmanager
from typing import AsyncIterator, List, Optional

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

        # FIXME: Bumping timeout to 15 minutes, but this should be configurable
        async with sse_client(
            url=server_config.command, headers=headers, sse_read_timeout=60 * 15
        ) as (
            read_stream,
            write_stream,
        ):
            async with ClientSession(read_stream, write_stream) as client_session:
                await client_session.initialize()
                yield client_session  # Yield the session for use

    except ExceptionGroup as e:
        logger.exception(f"TaskGroup failed in SSE client for {server_config.key}: {e}")
        for sub_extension in e.exceptions:
            logger.error(f"Sub-exception: {server_config.key}: {sub_extension}")
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


async def establish_mcp_sessions(
    tools_config: MCPToolsConfigModel, stack: AsyncExitStack
) -> List[MCPSession]:
    """
    Establish connections to MCP servers using the provided AsyncExitStack.
    """

    mcp_sessions: List[MCPSession] = []
    for server_config in tools_config.mcp_servers:
        # Check to see if the server is enabled
        if not server_config.enabled:
            logger.debug(f"Skipping disabled server: {server_config.key}")
            continue

        client_session: ClientSession | None = await stack.enter_async_context(
            connect_to_mcp_server(server_config)
        )
        if client_session:
            # Create an MCP session with the client session
            mcp_session = MCPSession(
                config=server_config, client_session=client_session
            )
            # Initialize the session to load tools, resources, etc.
            await mcp_session.initialize()
            # Add the session to the list of established sessions
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
