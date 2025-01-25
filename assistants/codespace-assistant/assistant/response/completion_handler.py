import json
import logging
import re
import time
from typing import List

import deepmerge
import openai_client
from mcp import ClientSession, Tool
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionToolMessageParam,
    ParsedChatCompletion,
)
from semantic_workbench_api_model.workbench_model import (
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from ..config import AssistantConfigModel
from ..extensions.tools import (
    ToolCall,
    handle_tool_call,
)
from .models import StepResult
from .utils import (
    extract_content_from_tool_calls,
    get_response_duration_message,
    get_token_usage_message,
)

logger = logging.getLogger(__name__)


async def handle_completion(
    step_result: StepResult,
    completion: ParsedChatCompletion | ChatCompletion,
    mcp_sessions: List[ClientSession],
    mcp_tools: List[Tool],
    context: ConversationContext,
    config: AssistantConfigModel,
    silence_token: str,
    method_metadata_key: str,
    response_start_time: float,
) -> StepResult:
    # helper function for handling errors
    async def handle_error(error_message: str) -> StepResult:
        await context.send_messages(
            NewConversationMessage(
                content=error_message,
                message_type=MessageType.notice,
                metadata=step_result.metadata,
            )
        )
        step_result.status = "error"
        return step_result

    # Get service and request configuration for generative model
    generative_request_config = config.generative_ai_client_config.request_config

    # get the total tokens used for the completion
    completion_total_tokens = completion.usage.total_tokens if completion.usage else 0

    response_content: list[str] = []

    if (completion.choices[0].message.content is not None) and (completion.choices[0].message.content.strip() != ""):
        response_content.append(completion.choices[0].message.content)

    # check if the completion has tool calls
    tool_calls: list[ToolCall] = []
    if completion.choices[0].message.tool_calls:
        ai_context, tool_calls = extract_content_from_tool_calls([
            ToolCall(
                id=tool_call.id,
                name=tool_call.function.name,
                arguments=json.loads(
                    tool_call.function.arguments,
                ),
            )
            for tool_call in completion.choices[0].message.tool_calls
        ])
        if ai_context is not None and ai_context.strip() != "":
            response_content.append(ai_context)

    content = "\n\n".join(response_content)

    # update the metadata with debug information
    deepmerge.always_merger.merge(
        step_result.metadata,
        {
            "debug": {
                method_metadata_key: {
                    "response": completion.model_dump() if completion else "[no response from openai]",
                },
            },
        },
    )

    # Add tool calls to the metadata
    deepmerge.always_merger.merge(
        step_result.metadata,
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
        step_result.metadata,
        {
            "footer_items": footer_items,
        },
    )

    # Set the conversation tokens for the turn result
    step_result.conversation_tokens = completion_total_tokens

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
                message_type=MessageType.chat,
                metadata=step_result.metadata,
            )
        )

    # Check for tool calls
    if len(tool_calls) == 0:
        # No tool calls, exit the loop
        step_result.status = "final"
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
            deepmerge.always_merger.merge(step_result.metadata, tool_call_result.metadata)

            # Add the token count for the tool call result to the total token count
            step_result.conversation_tokens += openai_client.num_tokens_from_messages(
                messages=[
                    ChatCompletionToolMessageParam(
                        role="tool",
                        content=tool_call_result.content,
                        tool_call_id=tool_call.id,
                    )
                ],
                model=generative_request_config.model,
            )

            # Add the tool_result payload to metadata
            deepmerge.always_merger.merge(
                step_result.metadata,
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
                    message_type=MessageType.note,
                    metadata=step_result.metadata,
                )
            )

    return step_result
