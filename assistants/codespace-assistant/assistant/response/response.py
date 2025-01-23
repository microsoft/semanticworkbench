import logging
import re
import time
from contextlib import AsyncExitStack
from typing import Any, List, Literal

import deepmerge
from assistant_extensions.ai_clients.model import CompletionMessage
from assistant_extensions.attachments import AttachmentsExtension
from attr import dataclass
from mcp import ClientSession, Tool
from semantic_workbench_api_model.workbench_model import (
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from ..config import AssistantConfigModel
from ..extensions.tools import (
    establish_mcp_sessions,
    get_mcp_server_prompts,
    handle_tool_call,
    retrieve_tools_from_sessions,
)
from .providers.openai_response_provider import OpenAIResponseProvider
from .utils import (
    build_system_message_content,
    conversation_message_to_completion_messages,
    get_history_messages,
    get_response_duration_message,
    get_token_usage_message,
    num_tokens_from_messages,
)

logger = logging.getLogger(__name__)


@dataclass
class TurnResult:
    status: Literal["final", "error", "continue"]
    conversation_tokens: int = 0


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
        completed_within_max_steps = False
        step_count = 0

        # Loop until the conversation is complete or the maximum number of steps is reached
        while step_count < max_steps:
            step_count += 1

            turn_result = await next_turn(
                mcp_sessions=mcp_sessions,
                mcp_tools=mcp_tools,
                mcp_prompts=mcp_prompts,
                attachments_extension=attachments_extension,
                context=context,
                config=config,
                metadata=metadata,
            )

            if turn_result.status == "final":
                completed_within_max_steps = True
                break

        # If the conversation did not complete within the maximum number of steps, send a message to the user
        if not completed_within_max_steps:
            await context.send_messages(
                NewConversationMessage(
                    content=config.extensions_config.tools.max_steps_truncation_message,
                    message_type=MessageType.notice,
                    metadata=metadata,
                )
            )

    # Log the completion of the conversation
    logger.info("Conversation completed.")


async def next_turn(
    mcp_sessions: List[ClientSession],
    mcp_tools: List[Tool],
    mcp_prompts: List[str],
    attachments_extension: AttachmentsExtension,
    context: ConversationContext,
    config: AssistantConfigModel,
    metadata: dict[str, Any],
) -> TurnResult:
    turn_result = TurnResult(status="continue")

    # Ensure that the metadata is a copy to prevent modification of the original
    metadata = metadata.copy()

    # helper function for handling errors
    async def handle_error(error_message: str) -> TurnResult:
        await context.send_messages(
            NewConversationMessage(
                content=error_message,
                message_type=MessageType.notice,
                metadata=metadata,
            )
        )
        turn_result.status = "error"

        return turn_result

    # Get response provider and request configuration for generative model
    generative_response_provider = OpenAIResponseProvider(
        conversation_context=context,
        assistant_config=config,
        openai_client_config=config.generative_ai_client_config,
    )
    generative_request_config = config.generative_ai_client_config.request_config

    # # Get response provider and request configuration for reasoning model
    # reasoning_response_provider = OpenAIResponseProvider(
    #     conversation_context=context,
    #     assistant_config=config,
    #     openai_client_config=config.reasoning_ai_client_config,
    # )
    # reasoning_request_config = config.reasoning_ai_client_config.request_config

    # Define the metadata key for any metadata created within this method
    method_metadata_key = "respond_to_conversation"

    # Track the start time of the response generation
    response_start_time = time.time()

    # Get the list of conversation participants
    participants_response = await context.get_participants(include_inactive=True)
    participants = participants_response.participants

    # Establish a token to be used by the AI model to indicate no response
    silence_token = "{{SILENCE}}"

    # Build system message content
    system_message_content = build_system_message_content(config, context, participants, silence_token)

    # Add MCP Server prompts to the system message content
    if len(mcp_prompts) > 0:
        system_message_content = "\n\n".join([system_message_content, *mcp_prompts])

    completion_messages: List[CompletionMessage] = [
        CompletionMessage(
            role="system",
            content=system_message_content,
        )
    ]

    token_count = 0

    # Calculate the token count for the messages so far
    result = await num_tokens_from_messages(
        context=context,
        response_provider=generative_response_provider,
        messages=completion_messages,
        model=generative_request_config.model,
        metadata=metadata,
        metadata_key="system_message",
    )
    if result is not None:
        token_count += result.count
    else:
        return await handle_error("Could not calculate token count for system message.")

    # Generate the attachment messages
    attachment_messages = await attachments_extension.get_completion_messages_for_attachments(
        context,
        config=config.extensions_config.attachments,
    )

    # Add attachment messages
    completion_messages.extend(attachment_messages)

    result = await num_tokens_from_messages(
        context=context,
        response_provider=generative_response_provider,
        messages=attachment_messages,
        model=generative_request_config.model,
        metadata=metadata,
        metadata_key="attachment_messages",
    )
    if result is not None:
        token_count += result.count
    else:
        return await handle_error("Could not calculate token count for attachment messages.")

    # Calculate available tokens
    available_tokens = generative_request_config.max_tokens - generative_request_config.response_tokens

    # Get history messages
    history_messages = await get_history_messages(
        response_provider=generative_response_provider,
        context=context,
        participants=participants_response.participants,
        converter=conversation_message_to_completion_messages,
        model=generative_request_config.model,
        token_limit=available_tokens - token_count,
    )

    # Add history messages
    completion_messages.extend(history_messages)

    # Check token count
    result = await num_tokens_from_messages(
        context=context,
        response_provider=generative_response_provider,
        messages=completion_messages,
        model=generative_request_config.model,
        metadata=metadata,
        metadata_key=method_metadata_key,
    )
    if result is None:
        return await handle_error("Could not calculate token count for history messages.")
    elif result.count > available_tokens:
        return await handle_error(
            f"You've exceeded the token limit of {generative_request_config.max_tokens} in this conversation "
            f"({result.count}). This assistant does not support recovery from this state. "
            "Please start a new conversation and let us know you ran into this."
        )

    # Generate AI response
    try:
        response_result = await generative_response_provider.get_generative_response(
            messages=completion_messages,
            metadata_key=f"{method_metadata_key}:request",
            mcp_tools=mcp_tools,
        )
    except Exception as e:
        logger.exception(f"Error generating AI response: {e}")
        return await handle_error("An error occurred while generating your response.")

    # Safely assign values to prevent unbound issues
    content = response_result.content if response_result.content else ""
    tool_calls = response_result.tool_calls if response_result.tool_calls else []
    message_type = response_result.message_type if response_result.message_type else MessageType.chat
    completion_total_tokens = response_result.completion_total_tokens if response_result.completion_total_tokens else 0

    # Merge the metadata from the response with the existing metadata
    deepmerge.always_merger.merge(metadata, response_result.metadata)

    # Add tool calls to the metadata
    deepmerge.always_merger.merge(
        metadata,
        {
            "tool_calls": [tool_call.to_dict() for tool_call in tool_calls],
        },
    )

    # Create the footer items for the response
    footer_items = []

    # Add the token usage message to the footer items
    if completion_total_tokens > 0:
        footer_items.append(get_token_usage_message(generative_request_config.max_tokens, completion_total_tokens))

    # Track the end time of the response generation and calculate duration
    response_end_time = time.time()
    response_duration = response_end_time - response_start_time

    # Add the response duration to the footer items
    footer_items.append(get_response_duration_message(response_duration))

    # Update the metadata with the footer items
    deepmerge.always_merger.merge(
        metadata,
        {
            "footer_items": footer_items,
        },
    )

    # Set the conversation tokens for the turn result
    turn_result.conversation_tokens = completion_total_tokens

    # strip out the username from the response
    if content.startswith("["):
        content = re.sub(r"\[.*\]:\s", "", content)

    # Handle silence token
    if content.replace(" ", "") == silence_token or content.strip() == "":
        # No response from the AI, nothing to send
        pass

    # Send the AI's response to the conversation
    else:
        await context.send_messages(
            NewConversationMessage(
                content=content,
                message_type=message_type,
                metadata=metadata,
            )
        )

    # Check for tool calls
    if len(tool_calls) == 0:
        # No tool calls, exit the loop
        turn_result.status = "final"
    else:
        # Handle tool calls
        tool_call_count = 0
        for tool_call in tool_calls:
            tool_call_count += 1
            try:
                tool_call_result = await handle_tool_call(
                    mcp_sessions,
                    tool_call,
                    mcp_tools,
                    f"{method_metadata_key}:request:tool_call_{tool_call_count}",
                )
            except Exception as e:
                logger.exception(f"Error handling tool call: {e}")
                return await handle_error("An error occurred while handling the tool call.")

            # Update content and metadata with tool call result metadata
            deepmerge.always_merger.merge(metadata, tool_call_result.metadata)

            # Get the token count for the tool call result
            tool_call_result_tokens = await num_tokens_from_messages(
                context=context,
                response_provider=generative_response_provider,
                messages=[
                    CompletionMessage(
                        role="tool",
                        content=tool_call_result.content,
                    )
                ],
                model=generative_request_config.model,
                metadata=metadata,
                metadata_key=f"{method_metadata_key}:tool_call_{tool_call_count}",
            )

            # Add the token count for the tool call result to the total token count
            if tool_call_result_tokens is not None:
                turn_result.conversation_tokens += tool_call_result_tokens.count
            else:
                return await handle_error("Could not calculate token count for tool call result.")

            # Add the tool_result payload to metadata
            deepmerge.always_merger.merge(
                metadata,
                {
                    "tool_result": {
                        "content": tool_call_result.content,
                        "tool_call_id": tool_call.id,
                    },
                },
            )

            await context.send_messages(
                NewConversationMessage(
                    content=tool_call_result.content,
                    message_type=MessageType.tool_result,
                    metadata=metadata,
                )
            )

    return turn_result
