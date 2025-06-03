import logging
from contextlib import AsyncExitStack, asynccontextmanager
from typing import AsyncGenerator

from assistant_extensions.mcp import (
    ExtendedCallToolRequestParams,
    MCPClientSettings,
    MCPServerConfig,
    MCPSession,
    establish_mcp_sessions,
    handle_mcp_tool_call,
    list_roots_callback_for,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from ..config import AssistantConfigModel
from ..response.models import ChatMessageProvider

logger = logging.getLogger(__name__)


def get_whiteboard_service_config(config: AssistantConfigModel) -> MCPServerConfig:
    """
    Get the memory whiteboard server configuration from the assistant config.
    If no personal server is configured with key 'memory-whiteboard', return the hosted server configuration.
    """
    return next(
        (
            server_config
            for server_config in config.tools.personal_mcp_servers
            if server_config.key == "memory-whiteboard"
        ),
        config.tools.hosted_mcp_servers.memory_whiteboard,
    )


async def notify_whiteboard(
    context: ConversationContext,
    server_config: MCPServerConfig,
    attachment_message_provider: ChatMessageProvider,
    chat_message_provider: ChatMessageProvider,
) -> None:
    if not server_config.enabled:
        return

    async with (
        whiteboard_mcp_session(context, server_config=server_config) as whiteboard_session,
        context.state_updated_event_after("whiteboard"),
    ):
        result = await handle_mcp_tool_call(
            mcp_sessions=[whiteboard_session],
            tool_call=ExtendedCallToolRequestParams(
                id="whiteboard",
                name="notify_user_message",
                arguments={
                    "attachment_messages": (await attachment_message_provider(0, "gpt-4o")).messages,
                    "chat_messages": (await chat_message_provider(30_000, "gpt-4o")).messages,
                },
            ),
            method_metadata_key="whiteboard",
        )
        logger.debug("memory-whiteboard result: %s", result)


@asynccontextmanager
async def whiteboard_mcp_session(
    context: ConversationContext, server_config: MCPServerConfig
) -> AsyncGenerator[MCPSession, None]:
    async with AsyncExitStack() as stack:
        mcp_sessions = await establish_mcp_sessions(
            client_settings=[
                MCPClientSettings(
                    server_config=server_config,
                    list_roots_callback=list_roots_callback_for(
                        context=context,
                        server_config=server_config,
                    ),
                )
            ],
            stack=stack,
        )
        yield mcp_sessions[0]
