import logging
from contextlib import AsyncExitStack
from typing import Any, List

from assistant_extensions.attachments import AttachmentsExtension
from assistant_extensions.mcp import MCPSession, establish_mcp_sessions, get_mcp_server_prompts, refresh_mcp_sessions
from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from ..config import AssistantConfigModel
from .step_handler import next_step
from .utils import get_ai_client_configs

logger = logging.getLogger(__name__)


async def respond_to_conversation(
    message: ConversationMessage,
    attachments_extension: AttachmentsExtension,
    context: ConversationContext,
    config: AssistantConfigModel,
    metadata: dict[str, Any] = {},
) -> None:
    """
    Perform a multi-step response to a conversation message using dynamically loaded MCP servers with
    support for multiple tool invocations.
    """

    async with AsyncExitStack() as stack:
        # If tools are enabled, establish connections to the MCP servers
        mcp_sessions: List[MCPSession] = []

        async def error_handler(server_config, error) -> None:
            logger.error(f"Failed to connect to MCP server {server_config.key}: {error}")
            # Also notify the user about this server failure here.
            await context.send_messages(
                NewConversationMessage(
                    content=f"Failed to connect to MCP server {server_config.key}: {error}",
                    message_type=MessageType.notice,
                    metadata=metadata,
                )
            )

        if config.extensions_config.tools.enabled:
            mcp_sessions = await establish_mcp_sessions(
                tools_config=config.extensions_config.tools,
                stack=stack,
                error_handler=error_handler
            )

            if len(config.extensions_config.tools.mcp_servers) > 0 and len(mcp_sessions) == 0:
                # No MCP servers are available, so we should not continue
                logger.error("No MCP servers are available.")
                return

        # Retrieve prompts from the MCP servers
        mcp_prompts = get_mcp_server_prompts(config.extensions_config.tools)

        # Initialize a loop control variable
        max_steps = config.extensions_config.tools.max_steps
        interrupted = False
        encountered_error = False
        completed_within_max_steps = False
        step_count = 0

        # TODO: This is a temporary hack to allow directing the request to the reasoning model
        request_type = "reasoning" if message.content.startswith("reason:") else "generative"

        # Get the AI client configuration based on the request type
        request_config, service_config = get_ai_client_configs(config, request_type)

        # Loop until the response is complete or the maximum number of steps is reached
        while step_count < max_steps:
            step_count += 1

            # Check to see if we should interrupt our flow
            last_message = await context.get_messages(limit=1, message_types=[MessageType.chat])

            if step_count > 1 and last_message.messages[0].sender.participant_id != context.assistant.id:
                # The last message was from a sender other than the assistant, so we should
                # interrupt our flow as this would have kicked off a new response from this
                # assistant with the new message in mind and that process can decide if it
                # should continue with the current flow or not.
                interrupted = True
                logger.info("Response interrupted.")
                break

            # Reconnect to the MCP servers if they were disconnected
            mcp_sessions = await refresh_mcp_sessions(mcp_sessions)

            step_result = await next_step(
                mcp_sessions=mcp_sessions,
                mcp_prompts=mcp_prompts,
                attachments_extension=attachments_extension,
                context=context,
                request_config=request_config,
                service_config=service_config,
                prompts_config=config.prompts,
                tools_config=config.extensions_config.tools,
                attachments_config=config.extensions_config.attachments,
                metadata=metadata,
                metadata_key=f"respond_to_conversation:step_{step_count}",
            )

            if step_result.status == "error":
                encountered_error = True
                break

            if step_result.status == "final":
                completed_within_max_steps = True
                break

        # If the response did not complete within the maximum number of steps, send a message to the user
        if not completed_within_max_steps and not encountered_error and not interrupted:
            await context.send_messages(
                NewConversationMessage(
                    content=config.extensions_config.tools.max_steps_truncation_message,
                    message_type=MessageType.notice,
                    metadata=metadata,
                )
            )
            logger.info("Response stopped early due to maximum steps.")

    # Log the completion of the response
    logger.info("Response completed.")
