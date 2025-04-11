import datetime
import logging
import pathlib
import zoneinfo

from mcp import ClientCapabilities, RootsCapability, ServerSession
from mcp.server.fastmcp import Context, FastMCP
from mcp_extensions.server import storage
from pydantic import AnyUrl, BaseModel

from .config import settings

logger = logging.getLogger(__name__)

# Set the name of the MCP server
server_name = "Memory - User Bio MCP Server"


class UserBioMemory(BaseModel):
    """
    A dataclass representing the memory of a user.
    This is used to store long-term details about the user.
    """

    date: datetime.date
    memory: str


class MemoryBank(BaseModel):
    """
    A dataclass representing a bank of memories.
    This is used to store multiple memories for a user.
    """

    memories: list[UserBioMemory] = []


class SessionConfig(BaseModel):
    user_timezone: datetime.tzinfo | None
    session_id: str


memory_uri = "resource://memory/user-bio"


def create_mcp_server() -> FastMCP:
    # Initialize FastMCP with debug logging.
    mcp = FastMCP(name=server_name, log_level=settings.log_level)

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
        session_config = await get_session_config(ctx)

        memory_date = get_user_date(user_timezone=session_config.user_timezone)

        memory_entry = UserBioMemory(
            date=memory_date,
            memory=memory,
        )

        memory_bank = await read_memory_bank(session_config=session_config)
        memory_bank.memories.append(memory_entry)
        await write_memory_bank(session_config=session_config, state=memory_bank)

        await ctx.session.send_resource_updated(uri=AnyUrl(memory_uri))

        return "Memory stored successfully."

    @mcp.tool()
    async def bio_forget(memory: str) -> str:
        """
        Forget a memory. This is used to remove long-term details about the user. Pass a specific memory to remove it.
        """

        ctx = mcp.get_context()
        session_config = await get_session_config(ctx)

        memory_bank = await read_memory_bank(session_config=session_config)

        original_length = len(memory_bank.memories)
        memory_bank.memories = [entry for entry in memory_bank.memories if entry.memory != memory]
        found = len(memory_bank.memories) < original_length

        if not found:
            return "Memory not found."

        await write_memory_bank(session_config=session_config, state=memory_bank)
        await ctx.session.send_resource_updated(uri=AnyUrl(memory_uri))

        return "Memory forgotten successfully."

    @mcp.resource(uri=memory_uri, name="user-bio", description="Long-term memories about the user.")
    @mcp.prompt(name="user-bio", description="Long-term memories about the user.")
    async def get_bio_prompt() -> str:
        ctx = mcp.get_context()
        session_config = await get_session_config(ctx)

        memory_bank = await read_memory_bank(session_config=session_config)

        if not memory_bank.memories:
            return "No memories saved."

        # Sort memories by date
        session_memories = sorted(memory_bank.memories, key=lambda x: x.date)

        # Format the memories into a string
        formatted_memories = "\n".join(f"[{memory.date}] {memory.memory}" for memory in session_memories)

        return f"Here are your memories about the user:\n{formatted_memories}"

    return mcp


def path_for_memory_bank(session_config: SessionConfig) -> pathlib.Path:
    return pathlib.Path(storage.settings.root) / session_config.session_id / "memory_bank.json"


async def read_memory_bank(session_config: SessionConfig) -> MemoryBank:
    """
    Read the memory bank from the storage.
    """
    memory_bank_path = path_for_memory_bank(session_config)
    state = storage.read_model(file_path=memory_bank_path, cls=MemoryBank) or MemoryBank()
    return state


async def write_memory_bank(session_config: SessionConfig, state: MemoryBank) -> None:
    """
    Write the memory bank to the storage.
    """
    memory_bank_path = path_for_memory_bank(session_config)
    storage.write_model(file_path=memory_bank_path, value=state)


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
