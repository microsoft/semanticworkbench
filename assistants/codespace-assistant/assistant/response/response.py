import logging
from contextlib import AsyncExitStack
from typing import Any, List

from assistant_extensions.attachments import AttachmentsExtension
from mcp import ClientSession
from semantic_workbench_api_model.workbench_model import (
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from ..config import AssistantConfigModel
from ..extensions.tools import (
    establish_mcp_sessions,
    get_mcp_server_prompts,
    retrieve_tools_from_sessions,
)
from .step_handler import next_step

logger = logging.getLogger(__name__)


async def respond_to_conversation(
    attachments_extension: AttachmentsExtension,
    context: ConversationContext,
    config: AssistantConfigModel,
    metadata: dict[str, Any] = {},
) -> None:
    """
    Respond to a conversation message using dynamically loaded MCP servers with support for multiple tool invocations.
    """

    async with AsyncExitStack() as stack:
        # If tools are enabled, establish connections to the MCP servers
        mcp_sessions: List[ClientSession] = []
        if config.extensions_config.tools.enabled:
            mcp_sessions = await establish_mcp_sessions(stack)
            if not mcp_sessions:
                await context.send_messages(
                    NewConversationMessage(
                        content="Unable to connect to any MCP servers. Please ensure the servers are running.",
                        message_type=MessageType.notice,
                        metadata=metadata,
                    )
                )
                return

        # Retrieve prompts from the MCP servers
        mcp_prompts = get_mcp_server_prompts()

        # Retrieve tools from the MCP sessions
        mcp_tools = await retrieve_tools_from_sessions(mcp_sessions)

        # Initialize a loop control variable
        max_steps = config.extensions_config.tools.max_steps
        encountered_error = False
        completed_within_max_steps = False
        step_count = 0

        # Loop until the conversation is complete or the maximum number of steps is reached
        while step_count < max_steps:
            step_count += 1

            step_result = await next_step(
                mcp_sessions=mcp_sessions,
                mcp_tools=mcp_tools,
                mcp_prompts=mcp_prompts,
                attachments_extension=attachments_extension,
                context=context,
                config=config,
                metadata=metadata,
                metadata_key=f"respond_to_conversation:step_{step_count}",
            )

            if step_result.status == "error":
                encountered_error = True
                break

            if step_result.status == "final":
                completed_within_max_steps = True
                break

        # If the conversation did not complete within the maximum number of steps, send a message to the user
        if not completed_within_max_steps and not encountered_error:
            await context.send_messages(
                NewConversationMessage(
                    content=config.extensions_config.tools.max_steps_truncation_message,
                    message_type=MessageType.notice,
                    metadata=metadata,
                )
            )

    # Log the completion of the conversation
    logger.info("Conversation completed.")
