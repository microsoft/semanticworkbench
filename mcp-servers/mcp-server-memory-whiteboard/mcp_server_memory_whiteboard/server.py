import asyncio
import datetime
import logging
import pathlib
from textwrap import dedent
from typing import Annotated, Any, Iterable
from urllib.parse import unquote

import openai_client
from mcp import ClientCapabilities, RootsCapability, ServerSession
from mcp.server.fastmcp import Context, FastMCP
from mcp_extensions.server import storage
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from openai_client import (
    OpenAIRequestConfig,
    azure_openai_service_config_construct,
    completion_structured,
    num_tokens_from_message,
)
from pydantic import BaseModel, Field
from semantic_workbench_assistant.config import first_env_var

from .config import settings

logger = logging.getLogger(__name__)

# Set the name of the MCP server
server_name = "Whiteboard Memory MCP Server"


class WhiteboardStateModel(BaseModel):
    content: str = ""
    timestamp: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    metadata: dict[str, Any] = {}


class SessionConfig(BaseModel):
    session_id: str


class Notification(BaseModel):
    attachment_messages: list[ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam]
    chat_messages: list[ChatCompletionMessageParam]
    session_config: SessionConfig


def create_mcp_server() -> FastMCP:
    mcp = FastMCP(name=server_name, log_level=settings.log_level)

    notification_queue = asyncio.Queue[Notification]()

    @mcp.tool()
    async def notify_user_message(
        attachment_messages: list[ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam],
        chat_messages: list[ChatCompletionMessageParam],
    ) -> str:
        mcp.get_context().session.client_params
        session_config = await get_session_config(mcp.get_context())
        await notification_queue.put(
            Notification(
                attachment_messages=attachment_messages, chat_messages=chat_messages, session_config=session_config
            )
        )
        await ensure_notification_task_started(mcp, notification_queue)

        return "Notification received"

    @mcp.prompt("memory:whiteboard", description="Whiteboard content as a prompt")
    async def whiteboard_memory_prompt() -> str:
        """
        Whiteboard content as a prompt.
        """
        session_config = await get_session_config(mcp.get_context())
        return (await read_whiteboard_state(session_config, timestamp=None)).content

    @mcp.resource("resource://memory/whiteboard", description="Whiteboard memory as a JSON resource")
    async def whiteboard_memory_resource() -> WhiteboardStateModel:
        """
        Whiteboard memory as a JSON resource.
        """
        session_config = await get_session_config(mcp.get_context())
        return await read_whiteboard_state(session_config, timestamp=None)

    @mcp.resource(
        "resource://memory/whiteboard/{timestamp}",
        description="Whiteboard memory as a JSON resource, as of the given timestamp",
    )
    async def whiteboard_memory_resource_by_timestamp(timestamp: str) -> WhiteboardStateModel:
        """
        Whiteboard memory as a JSON resource, as of the given timestamp.
        """
        decoded_timestamp = unquote(timestamp)
        timestamp_datetime = datetime.datetime.fromisoformat(decoded_timestamp)
        session_config = await get_session_config(mcp.get_context())
        return await read_whiteboard_state(session_config, timestamp=timestamp_datetime)

    return mcp


async def get_session_config(ctx: Context[ServerSession, object]) -> SessionConfig:
    """
    Get the session configuration from the client.
    """
    if not ctx.session.check_client_capability(ClientCapabilities(roots=RootsCapability())):
        logger.debug("Client does not support roots capability.")
        return SessionConfig(session_id="")

    list_roots_result = await ctx.session.list_roots()

    session_id: str = ""

    for root in list_roots_result.roots:
        match root.name:
            case "session-id":
                session_id = (root.uri.host or root.uri.path or "").strip("/")

    return SessionConfig(session_id=session_id)


def path_for_directory(session_config: SessionConfig) -> pathlib.Path:
    """
    Get the path for the directory where the whiteboard state is stored.
    """
    return pathlib.Path(storage.settings.root) / session_config.session_id


def timestamp_to_filename(timestamp: datetime.datetime) -> str:
    """
    Convert a timestamp to a filename.
    """
    return f"{timestamp.isoformat().replace(':', '-').replace('+', '--')}.json"


async def read_whiteboard_state(
    session_config: SessionConfig, timestamp: datetime.datetime | None
) -> WhiteboardStateModel:
    """
    Read the whiteboard state from the storage.
    """
    whiteboard_path = path_for_directory(session_config) / "whiteboard.json"
    if timestamp:
        first_timestamp_after = ""
        first_timestamp_before = ""
        for file in path_for_directory(session_config).glob("*.json"):
            if file.name == "whiteboard.json":
                continue

            if file.name <= timestamp_to_filename(timestamp):
                if not first_timestamp_before or file.name > first_timestamp_before:
                    first_timestamp_before = file.name
                continue

            if file.name > timestamp_to_filename(timestamp):
                if not first_timestamp_after or file.name < first_timestamp_after:
                    first_timestamp_after = file.name

        if first_timestamp_after or first_timestamp_before:
            whiteboard_path = path_for_directory(session_config) / (first_timestamp_after or first_timestamp_before)

    state = storage.read_model(file_path=whiteboard_path, cls=WhiteboardStateModel) or WhiteboardStateModel()
    return state


async def write_whiteboard_state(session_config: SessionConfig, state: WhiteboardStateModel) -> None:
    """
    Write the whiteboard state to the storage.
    """
    latest_path = path_for_directory(session_config) / "whiteboard.json"
    timestamp_path = path_for_directory(session_config) / timestamp_to_filename(state.timestamp)
    storage.write_model(file_path=latest_path, value=state)
    storage.write_model(file_path=timestamp_path, value=state)


async def process_notification_queue(notification_queue: asyncio.Queue[Notification]) -> None:
    """
    Process the notification queue.
    """
    while True:
        notification = await notification_queue.get()
        if notification is None:
            break

        try:
            await process_notification(notification)
        except Exception:
            logger.exception("error processing notification")

        # Mark the task as done
        notification_queue.task_done()


async def process_notification(notification: Notification) -> None:
    """
    Process the notification.
    """

    class WhiteboardModel(BaseModel):
        content: Annotated[str, Field(description="Content of the whiteboard")]

    current_whiteboard_state = await read_whiteboard_state(notification.session_config, None)

    model = first_env_var("azure_openai_model", "assistant__azure_openai_model") or "gpt-4.1"

    max_chat_token_count = 1024 * 6  # 6k tokens, similar to the v5 whiteboard limitations

    token_count = 0
    chat_completion_messages: list[ChatCompletionMessageParam] = []

    for message in reversed(notification.chat_messages):
        # remove the tool calls from the message
        message.pop("tool_calls", None)
        # ignore all tool call response messages
        if message["role"] == "tool":
            continue

        content = message.get("content")
        match content:
            case str():
                completion_message = message

            case Iterable():
                # the contents with iterables are parsed as pydantic ValidationIterator
                # (not sure why - i think it is something that the mcp library does)
                # for these, we need to convert them back to a list
                completion_message = {
                    "role": "user",
                    "content": [part for part in content],
                }

            case _:
                continue

        message_tokens = num_tokens_from_message(message, model=model)

        token_count += message_tokens
        if token_count > max_chat_token_count:
            break

        chat_completion_messages.append(completion_message)  # type: ignore

    chat_completion_messages = list(reversed(chat_completion_messages))

    completion_messages = [
        *chat_completion_messages,
        {
            "role": "developer",
            "content": dedent(
                """
                Extract important information from the chat history between the assistant and user(s). It should be used to update the whiteboard content for the assistant.

                The assistant has access to look up information in the rest of the chat history, but this is based upon semantic similarity to current user request, so the whiteboard content is for information that should always be available to the bot, even if it is not directly semantically related to the current user request.

                The whiteboard is limited in size, so it is important to keep it up to date with the most important information and it is ok to remove information that is no longer relevant.  It is also ok to leave the whiteboard blank if there is no information important enough be added to the whiteboard.

                Think of the whiteboard as the type of content that might be written down on a whiteboard during a meeting. It is not a transcript of the conversation, but rather only the most important information that is relevant to the current task at hand.

                Use markdown to format the whiteboard content.  For example, you can use headings, lists, and links to other resources.

                Whiteboard content:
                <WHITEBOARD>
                {current_whiteboard}
                </WHITEBOARD>
                """
            )
            .strip()
            .format(
                current_whiteboard=current_whiteboard_state.content,
            ),
        },
        {
            "role": "developer",
            "content": dedent(
                """
                Please provide updated whiteboard content based upon information extracted from the chat history.  Do not provide any information that is not already in the chat history and do not answer any pending requests.
                """
            ).strip(),
        },
    ]

    service_config = azure_openai_service_config_construct(default_deployment=model)
    request_config = OpenAIRequestConfig(
        max_tokens=128_000,
        # artificially limit the response tokens to 1k to limit the size of the whiteboard
        # and match the v5 whiteboard implementation
        response_tokens=1024,
        model=model,
    )
    try:
        async with openai_client.create_client(service_config=service_config) as client:
            response = await completion_structured(
                async_client=client,
                messages=completion_messages,
                openai_model=request_config.model,
                max_completion_tokens=request_config.response_tokens,
                response_model=WhiteboardModel,
            )

            updated_whiteboard = WhiteboardStateModel(content=response.response.content, metadata=response.metadata)
            await write_whiteboard_state(notification.session_config, updated_whiteboard)

    except Exception:
        logger.exception("error executing LLM completion to update whiteboard")


async def ensure_notification_task_started(mcp: FastMCP, notification_queue: asyncio.Queue[Notification]) -> None:
    """
    Ensure the notification task is started.
    """
    if hasattr(mcp, "_notification_task"):
        # Task already started
        return

    task = asyncio.create_task(process_notification_queue(notification_queue))
    # store a reference to the task in the MCP server so it won't be garbage collected
    setattr(mcp, "_notification_task", task)
