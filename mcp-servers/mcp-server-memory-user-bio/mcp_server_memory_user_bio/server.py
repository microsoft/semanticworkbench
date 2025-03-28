import datetime
import logging
import zoneinfo
from collections import defaultdict
from dataclasses import dataclass

from mcp import ClientCapabilities, RootsCapability, ServerSession
from mcp.server.fastmcp import Context, FastMCP
from pydantic import AnyUrl

from .config import settings

logger = logging.getLogger(__name__)

# Set the name of the MCP server
server_name = "Memory - User Bio MCP Server"


@dataclass
class UserBioMemory:
    """
    A dataclass representing the memory of a user.
    This is used to store long-term details about the user.
    """

    date: datetime.date
    memory: str


@dataclass
class SessionConfig:
    user_timezone: datetime.tzinfo | None
    session_id: str


memory_uri = "resource://memory/user-bio"


def create_mcp_server() -> FastMCP:
    # Initialize FastMCP with debug logging.
    mcp = FastMCP(name=server_name, log_level=settings.log_level)

    memories: dict[str, list[UserBioMemory]] = defaultdict(lambda: [])

    @mcp.tool()
    async def bio(memory: str) -> str:
        """
        Remember long-term details about the user, such as their interests, preferences, experiences, or ongoing projects.
        *DO NOT* use it for short-term details like temporary tasks, one-time events, or what they're doing this weekend.
        *DO NOT* use it for sensitive or private information like passwords, financial info, personal addresses, or private keys.

        Always ensure that memories are:
        - Concise but informative – enough detail to be useful but not overly long.
        - Structured in a clear sentence – stating facts in a way that’s easy to recall and apply.
        - Contextually relevant – focused on long-term or recurring details.
        """

        ctx = mcp.get_context()
        client_roots = await get_session_config(ctx)

        memory_date = get_user_date(user_timezone=client_roots.user_timezone)

        memory_entry = UserBioMemory(
            date=memory_date,
            memory=memory,
        )

        memories[client_roots.session_id].append(memory_entry)

        await ctx.session.send_resource_updated(uri=AnyUrl(memory_uri))

        return "Memory stored successfully."

    @mcp.tool()
    async def bio_forget(memory: str) -> str:
        """
        Forget a memory. This is used to remove long-term details about the user. Pass a specific memory to remove it.
        """

        ctx = mcp.get_context()
        client_roots = await get_session_config(ctx)

        original_length = len(memories[client_roots.session_id])
        memories[client_roots.session_id] = [
            entry for entry in memories[client_roots.session_id] if entry.memory != memory
        ]
        found = len(memories[client_roots.session_id]) < original_length

        if not found:
            return "Memory not found."

        await ctx.session.send_resource_updated(uri=AnyUrl(memory_uri))

        return "Memory forgotten successfully."

    @mcp.resource(uri=memory_uri, name="user-bio", description="Long-term memories about the user.")
    @mcp.prompt(name="user-bio", description="Long-term memories about the user.")
    async def get_bio_prompt() -> str:
        ctx = mcp.get_context()
        client_roots = await get_session_config(ctx)

        if not memories[client_roots.session_id]:
            return "No memories saved."

        # Sort memories by date
        session_memories = sorted(memories[client_roots.session_id], key=lambda x: x.date)

        # Format the memories into a string
        formatted_memories = "\n".join(f"[{memory.date}] {memory.memory}" for memory in session_memories)

        return f"Here are your memories about the user:\n{formatted_memories}"

    return mcp


async def get_session_config(ctx: Context[ServerSession, object]) -> SessionConfig:
    """
    Get the session configuration from the client.
    """
    if not settings.enable_client_roots:
        return SessionConfig(user_timezone=None, session_id="")

    if not ctx.session.check_client_capability(ClientCapabilities(roots=RootsCapability())):
        logger.debug("Client does not support roots capability.")
        return SessionConfig(user_timezone=None, session_id="")

    list_roots_result = await ctx.session.list_roots()

    user_timezone: datetime.tzinfo | None = None
    session_id: str = ""

    for root in list_roots_result.roots:
        match root.name:
            case "user-timezone":
                timezone_str = str(root.uri).replace(root.uri.scheme, "")
                try:
                    user_timezone = zoneinfo.ZoneInfo(timezone_str)
                except ValueError:
                    logger.exception("invalid timezone in user-timezone root received from client: %s", root.uri)

            case "session-id":
                session_id = (root.uri.host or root.uri.path or "").strip("/")

    return SessionConfig(user_timezone=user_timezone, session_id=session_id)


def get_user_date(user_timezone: datetime.tzinfo | None) -> datetime.date:
    """
    Get the current date for the user's timezone, falling back to the server's timezone
    if user_timezone is not provided.
    """

    if not user_timezone:
        return datetime.date.today()

    return datetime.datetime.now(user_timezone).date()
