import asyncio
import logging
import pathlib
from textwrap import dedent
from typing import Annotated, Any

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
)
from pydantic import BaseModel, Field
from semantic_workbench_assistant.config import first_env_var

from .config import settings

logger = logging.getLogger(__name__)

# Set the name of the MCP server
server_name = "Whiteboard Memory MCP Server"


class WhiteboardStateModel(BaseModel):
    content: str = ""
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
        return (await read_whiteboard_state(session_config)).content

    @mcp.resource("resource://memory/whiteboard", description="Whiteboard memory as a JSON resource")
    async def whiteboard_memory_resource() -> WhiteboardStateModel:
        """
        Whiteboard memory as a JSON resource.
        """
        session_config = await get_session_config(mcp.get_context())
        return await read_whiteboard_state(session_config)

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


def path_for_whiteboard(session_config: SessionConfig) -> pathlib.Path:
    return pathlib.Path(storage.settings.root) / session_config.session_id / "whiteboard.json"


async def read_whiteboard_state(session_config: SessionConfig) -> WhiteboardStateModel:
    """
    Read the whiteboard state from the storage.
    """
    whiteboard_path = path_for_whiteboard(session_config)
    state = storage.read_model(file_path=whiteboard_path, cls=WhiteboardStateModel) or WhiteboardStateModel()
    return state


async def write_whiteboard_state(session_config: SessionConfig, state: WhiteboardStateModel) -> None:
    """
    Write the whiteboard state to the storage.
    """
    whiteboard_path = path_for_whiteboard(session_config)
    storage.write_model(file_path=whiteboard_path, value=state)


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

    current_whiteboard_state = await read_whiteboard_state(notification.session_config)

    attachment_completion_messages = []
    for message in notification.attachment_messages:
        content = message.get("content")
        if not content:
            continue

        if isinstance(content, str):
            attachment_completion_messages.append({
                "role": "user",
                "content": content,
            })
            continue

        attachment_completion_messages.append({
            "role": "user",
            "content": [part for part in content],
        })

    chat_completion_messages = []
    for message in notification.chat_messages:
        content = message.get("content")
        if not content:
            continue

        if isinstance(content, str):
            chat_completion_messages.append({
                "role": "user",
                "content": content,
            })
            continue

        chat_completion_messages.append({
            "role": "user",
            "content": [part for part in content],
        })

    completion_messages = [
        *attachment_completion_messages,
        *notification.chat_messages,
        # {
        #     "role": "user",
        #     "content": "<CHAT_HISTORY>\n"
        #     + "\n".join([
        #         str(message.get("content")) for message in notification.chat_messages if message.get("content")
        #     ])
        #     + "\n</CHAT_HISTORY>",
        # },
        {
            "role": "developer",
            "content": dedent(
                """
                You are an expert note-taker and whiteboard manager. You are responsible for keeping the
                whiteboard up to date with the most important information from the <CHAT_HISTORY>. The
                whiteboard is a summary of the most important information that is relevant to the current
                task at hand. It is not a transcript of the conversation, but rather only the most
                important information that is relevant to the current task at hand.

                The whiteboard is limited in size, so it is important to keep it up to date with the most
                important information and it is ok to remove information that is no longer relevant. It is
                also ok to leave the whiteboard blank if there is no information important enough to be added
                to the whiteboard.

                Think of the whiteboard as the type of content that might be written down on a whiteboard
                during a meeting. It is not a transcript of the conversation, but rather only the most
                important information that is relevant to the current task at hand.

                Use markdown to format the whiteboard content. For example, you can use headings, lists,
                and links to other resources.

                Please provide updated whiteboard content based upon the current whiteboard and relevant
                information extracted from the <CHAT_HISTORY>.

                - DO include decisions made, if any
                - DO include historical tasks
                - DO include historical decisions, unless they have been superseded with new decisions
                - DO NOT include any information that is not in the <CHAT_HISTORY>
                - DO NOT suggest next steps or actions
                - DO NOT answer any questions

                The current whiteboard content, which you will be updating, is as follows:
                <WHITEBOARD>
                """
                + current_whiteboard_state.content
                + """
                </WHITEBOARD>

                Now go ahead and do you job and give me the updated whiteboard content.
                """
            ).strip(),
        },
    ]

    service_config = azure_openai_service_config_construct(default_deployment="gpt-4o")
    request_config = OpenAIRequestConfig(
        max_tokens=128_000,
        response_tokens=8196,
        model=first_env_var("azure_openai_model", "assistant__azure_openai_model") or "gpt-4o",
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
