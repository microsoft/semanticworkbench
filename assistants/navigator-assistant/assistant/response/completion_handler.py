import json
import logging
import re
from typing import Any

import deepmerge
from openai.types.chat import (
    ChatCompletion,
    ParsedChatCompletion,
)
from semantic_workbench_api_model.workbench_model import (
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from .models import SILENCE_TOKEN, CompletionHandlerResult
from .utils import (
    ExecutableTool,
    execute_tool,
    get_response_duration_message,
    get_token_usage_message,
)

logger = logging.getLogger(__name__)


async def handle_completion(
    completion: ParsedChatCompletion | ChatCompletion,
    context: ConversationContext,
    metadata_key: str,
    metadata: dict[str, Any],
    response_duration: float,
    max_tokens: int,
    tools: list[ExecutableTool],
) -> CompletionHandlerResult:
    """
    Handle the completion response from the AI model.
    This function processes the completion, possibly sending a conversation message, and executes tool calls if present.
    """

    # update the metadata with debug information
    deepmerge.always_merger.merge(
        metadata,
        {
            "debug": {
                metadata_key: {
                    "response": completion.model_dump(),
                },
            },
        },
    )

    # get the content from the completion
    content = (completion.choices[0].message.content or "").strip()

    # Create the footer items for the response
    footer_items = []

    # get the total tokens used for the completion
    if completion.usage and completion.usage.total_tokens > 0:
        # Add the token usage message to the footer items
        total_tokens = completion.usage.total_tokens
        completion_tokens = completion.usage.completion_tokens
        request_tokens = total_tokens - completion_tokens
        footer_items.append(
            get_token_usage_message(
                max_tokens=max_tokens,
                total_tokens=total_tokens,
                request_tokens=request_tokens,
                completion_tokens=completion_tokens,
            )
        )

        await context.update_conversation(
            metadata={
                "token_counts": {
                    "total": total_tokens,
                    "max": max_tokens,
                }
            }
        )

    # Add the response duration to the footer items
    footer_items.append(get_response_duration_message(response_duration))

    completion_message_metadata = metadata.copy()

    # Update the metadata with the footer items
    deepmerge.always_merger.merge(
        completion_message_metadata,
        {
            "footer_items": footer_items,
        },
    )

    # strip out the username from the response
    if content.startswith("["):
        content = re.sub(r"\[.*\]:\s", "", content).strip()

    # check if the completion has tool calls
    tool_calls = completion.choices[0].message.tool_calls or []

    # Add tool calls to the metadata
    deepmerge.always_merger.merge(
        completion_message_metadata,
        {
            "tool_calls": [tool_call.model_dump(mode="json") for tool_call in tool_calls],
        },
    )

    # Handle silence token
    if not content.startswith(SILENCE_TOKEN):
        # Send the AI's response to the conversation
        await context.send_messages(
            NewConversationMessage(
                content=content,
                message_type=MessageType.chat if content else MessageType.log,
                metadata=completion_message_metadata,
            )
        )

    # Check for tool calls
    if len(tool_calls) == 0:
        # No tool calls, exit the loop
        return CompletionHandlerResult(status="final")

    # Handle tool calls
    for tool_call_index, tool_call in enumerate(tool_calls):
        async with context.set_status(f"using tool `{tool_call.function.name}`..."):
            try:
                arguments = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                content = await execute_tool(
                    context=context, tools=tools, tool_name=tool_call.function.name, arguments=arguments
                )

            except Exception as e:
                logger.exception("error handling tool call '%s'", tool_call.function.name)
                deepmerge.always_merger.merge(
                    completion_message_metadata,
                    {
                        "debug": {
                            f"{metadata_key}:request:tool_call_{tool_call_index}": {
                                "error": str(e),
                            },
                        },
                    },
                )
                content = f"Error executing tool '{tool_call.function.name}': {e}"

        # Add the tool_result payload to metadata
        deepmerge.always_merger.merge(
            completion_message_metadata,
            {
                "tool_result": {
                    "content": content,
                    "tool_call_id": tool_call.id,
                },
            },
        )

        await context.send_messages(
            NewConversationMessage(
                content=content,
                message_type=MessageType.log,
                metadata=completion_message_metadata,
            )
        )

    return CompletionHandlerResult(
        status="continue",
    )
