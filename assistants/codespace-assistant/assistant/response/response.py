import logging
from contextlib import AsyncExitStack
from typing import Any

from assistant_extensions.attachments import AttachmentsExtension
from assistant_extensions.mcp import (
    MCPServerConnectionError,
    OpenAISamplingHandler,
    establish_mcp_sessions,
    get_enabled_mcp_server_configs,
    get_mcp_server_prompts,
    refresh_mcp_sessions,
)
from mcp.types import TextResourceContents
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
        # Get the AI client configurations for this assistant
        generative_ai_client_config = get_ai_client_configs(config, "generative")
        reasoning_ai_client_config = get_ai_client_configs(config, "reasoning")

        # TODO: This is a temporary hack to allow directing the request to the reasoning model
        # Currently we will only use the requested AI client configuration for the turn
        request_type = "reasoning" if message.content.startswith("reason:") else "generative"
        # Set a default AI client configuration based on the request type
        default_ai_client_config = (
            reasoning_ai_client_config if request_type == "reasoning" else generative_ai_client_config
        )
        # Set the service and request configurations for the AI client
        service_config = default_ai_client_config.service_config
        request_config = default_ai_client_config.request_config

        # Create a sampling handler for handling requests from the MCP servers
        sampling_handler = OpenAISamplingHandler(
            ai_client_configs=[
                generative_ai_client_config,
                reasoning_ai_client_config,
            ]
        )

        enabled_servers = []
        if config.tools.enabled:
            enabled_servers = get_enabled_mcp_server_configs(config.tools.mcp_servers)

        try:
            mcp_sessions = await establish_mcp_sessions(
                mcp_server_configs=enabled_servers,
                stack=stack,
                sampling_handler=sampling_handler.handle_message,
            )

        except MCPServerConnectionError as e:
            await context.send_messages(
                NewConversationMessage(
                    content=f"Failed to connect to MCP server {e.server_config.key}: {e}",
                    message_type=MessageType.notice,
                    metadata=metadata,
                )
            )
            return

        # Retrieve prompts from the MCP servers
        mcp_prompts = get_mcp_server_prompts(enabled_servers)

        # Initialize a loop control variable
        max_steps = config.tools.advanced.max_steps
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

            # Reconnect to the MCP servers if they were disconnected
            mcp_sessions = await refresh_mcp_sessions(mcp_sessions)

            memories: list[tuple[str, str]] = []
            for mcp_session in mcp_sessions:
                list_resources_result = await mcp_session.client_session.list_resources()
                for resource in list_resources_result.resources:
                    if resource.uri.host != "filesystem_edit":
                        continue
                    read_resource_result = await mcp_session.client_session.read_resource(resource.uri)

                    memory_content: str = ""
                    for content in read_resource_result.contents:
                        if not isinstance(content, TextResourceContents):
                            logger.warning(
                                "Unexpected content type for memory; uri: %s, type: %s", resource.uri, type(content)
                            )
                            continue
                        memory_content += content.text
                    memories.append((resource.name, memory_content))

            step_result = await next_step(
                sampling_handler=sampling_handler,
                mcp_sessions=mcp_sessions,
                mcp_prompts=mcp_prompts,
                memories=memories,
                attachments_extension=attachments_extension,
                context=context,
                request_config=request_config,
                service_config=service_config,
                prompts_config=config.prompts,
                tools_config=config.tools,
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
                    content=config.tools.advanced.max_steps_truncation_message,
                    message_type=MessageType.notice,
                    metadata=metadata,
                )
            )
            logger.info("Response stopped early due to maximum steps.")

    # Log the completion of the response
    logger.info("Response completed.")
