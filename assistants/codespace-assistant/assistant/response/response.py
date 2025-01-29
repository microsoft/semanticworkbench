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
    Perform a multi-step response to a conversation message using dynamically loaded MCP servers with
    support for multiple tool invocations.
    """

    async with AsyncExitStack() as stack:
        # If tools are enabled, establish connections to the MCP servers
        mcp_sessions: List[ClientSession] = []
        if config.extensions_config.tools.enabled:
            mcp_sessions = await establish_mcp_sessions(config.extensions_config.tools, stack)
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
        mcp_prompts = get_mcp_server_prompts(config.extensions_config.tools)

        # Retrieve tools from the MCP sessions
        mcp_tools = await retrieve_tools_from_sessions(mcp_sessions)

        # Initialize a loop control variable
        max_steps = config.extensions_config.tools.max_steps
        interrupted = False
        encountered_error = False
        completed_within_max_steps = False
        step_count = 0

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
