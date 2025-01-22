import logging
from contextlib import AsyncExitStack, asynccontextmanager
from typing import AsyncIterator, List, Optional

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from .__mcp_server_configs import mcp_server_configs
from .__model import MCPServerConfig

logger = logging.getLogger(__name__)


@asynccontextmanager
async def connect_to_mcp_server(server_config: MCPServerConfig) -> AsyncIterator[Optional[ClientSession]]:
    """Connect to a single MCP server defined in the config."""

    server_params = StdioServerParameters(command=server_config.command, args=server_config.args, env=server_config.env)
    try:
        logger.debug(
            f"Attempting to connect to {server_config.name} with command: {server_config.command} {' '.join(server_config.args)}"
        )
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                yield session  # Yield the session for use
    except Exception as e:
        logger.exception(f"Error connecting to {server_config.name}: {e}")
        yield None  # Yield None if connection fails


async def establish_mcp_sessions(stack: AsyncExitStack) -> List[ClientSession]:
    """
    Establish connections to MCP servers using the provided AsyncExitStack.
    """

    sessions: List[ClientSession] = []
    for server_config in mcp_server_configs:
        session: ClientSession | None = await stack.enter_async_context(connect_to_mcp_server(server_config))
        if session:
            sessions.append(session)
        else:
            logger.warning(f"Could not establish session with {server_config.name}")
    return sessions
