# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from dataclasses import dataclass
from typing import Any

import openai_client
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCallParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)
from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    ConversationParticipant,
    MessageType,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from .formatting_utils import format_message

logger = logging.getLogger(__name__)


@dataclass
class GetHistoryMessagesResult:
    messages: list[ChatCompletionMessageParam]
    token_count: int
    token_overage: int


def conversation_message_to_tool_message(
    message: ConversationMessage,
) -> ChatCompletionToolMessageParam | None:
    """
    Check to see if the message contains a tool result and return a tool message if it does.
    """
    tool_result = message.metadata.get("tool_result")
    if tool_result is not None:
        content = tool_result.get("content")
        tool_call_id = tool_result.get("tool_call_id")
        if content is not None and tool_call_id is not None:
            return ChatCompletionToolMessageParam(
                role="tool",
                content=content,
                tool_call_id=tool_call_id,
            )


def tool_calls_from_metadata(metadata: dict[str, Any]) -> list[ChatCompletionMessageToolCallParam] | None:
    """
    Get the tool calls from the message metadata.
    """
    if metadata is None or "tool_calls" not in metadata:
        return None

    tool_calls = metadata["tool_calls"]
    if not isinstance(tool_calls, list) or len(tool_calls) == 0:
        return None

    tool_call_params: list[ChatCompletionMessageToolCallParam] = []
    for tool_call in tool_calls:
        if not isinstance(tool_call, dict):
            try:
                tool_call = json.loads(tool_call)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse tool call from metadata: {tool_call}")
                continue

        id = tool_call["id"]
        name = tool_call["name"]
        arguments = json.dumps(tool_call["arguments"])
        if id is not None and name is not None and arguments is not None:
            tool_call_params.append(
                ChatCompletionMessageToolCallParam(
                    id=id,
                    type="function",
                    function={"name": name, "arguments": arguments},
                )
            )

    return tool_call_params


def conversation_message_to_assistant_message(
    message: ConversationMessage,
    participants: list[ConversationParticipant],
) -> ChatCompletionAssistantMessageParam:
    """
    Convert a conversation message to an assistant message.
    """
    assistant_message = ChatCompletionAssistantMessageParam(
        role="assistant",
        content=format_message(message, participants),
    )

    # get the tool calls from the message metadata
    tool_calls = tool_calls_from_metadata(message.metadata)
    if tool_calls:
        assistant_message["tool_calls"] = tool_calls

    return assistant_message


def conversation_message_to_user_message(
    message: ConversationMessage,
    participants: list[ConversationParticipant],
) -> ChatCompletionMessageParam:
    """
    Convert a conversation message to a user message.
    """
    return ChatCompletionUserMessageParam(
        role="user",
        content=format_message(message, participants),
    )


async def conversation_message_to_chat_message_params(
    context: ConversationContext, message: ConversationMessage, participants: list[ConversationParticipant]
) -> list[ChatCompletionMessageParam]:
    """
    Convert a conversation message to a list of chat message parameters.
    """

    # some messages may have multiple parts, such as a text message with an attachment
    chat_message_params: list[ChatCompletionMessageParam] = []

    # add the message to list, treating messages from a source other than this assistant as a user message
    if message.message_type == MessageType.note:
        # we are stuffing tool messages into the note message type, so we need to check for that
        tool_message = conversation_message_to_tool_message(message)
        if tool_message is not None:
            chat_message_params.append(tool_message)
        else:
            logger.warning(f"Failed to convert tool message to completion message: {message}")

    elif message.message_type == MessageType.log:
        # Assume log messages are dynamic ui choice messages which are treated as user messages
        user_message = conversation_message_to_user_message(message, participants)
        chat_message_params.append(user_message)

    elif message.sender.participant_id == context.assistant.id:
        # add the assistant message to the completion messages
        assistant_message = conversation_message_to_assistant_message(message, participants)
        chat_message_params.append(assistant_message)

    else:
        # add the user message to the completion messages
        user_message = conversation_message_to_user_message(message, participants)
        chat_message_params.append(user_message)

        # add the attachment message to the completion messages
        if message.filenames and len(message.filenames) > 0:
            # add a system message to indicate the attachments
            chat_message_params.append(
                ChatCompletionSystemMessageParam(
                    role="system", content=f"Attachment(s): {', '.join(message.filenames)}"
                )
            )

    return chat_message_params


async def get_history_messages(
    context: ConversationContext,
    participants: list[ConversationParticipant],
    model: str,
    token_limit: int | None = None,
) -> GetHistoryMessagesResult:
    """
    Get all messages in the conversation, formatted for use in a completion.
    """

    # each call to get_messages will return a maximum of 100 messages
    # so we need to loop until all messages are retrieved
    # if token_limit is provided, we will stop when the token limit is reached

    history = []
    token_count = 0
    before_message_id = None
    token_overage = 0

    while True:
        # get the next batch of messages, including chat and tool result messages
        messages_response = await context.get_messages(
            limit=100, before=before_message_id, message_types=[MessageType.chat, MessageType.note, MessageType.log]
        )
        messages_list = messages_response.messages

        # if there are no more messages, break the loop
        if not messages_list or messages_list.count == 0:
            break

        # set the before_message_id for the next batch of messages
        before_message_id = messages_list[0].id

        # messages are returned in reverse order, so we need to reverse them
        for message in reversed(messages_list):
            # format the message
            formatted_message_list = await conversation_message_to_chat_message_params(context, message, participants)
            formatted_messages_token_count = openai_client.num_tokens_from_messages(formatted_message_list, model=model)

            # if the token limit is not reached, or if the token limit is not provided
            if token_overage == 0 and token_limit and token_count + formatted_messages_token_count < token_limit:
                # increment the token count
                token_count += formatted_messages_token_count

                # insert the formatted messages onto the top of the history list
                history = formatted_message_list + history

            else:
                # on first time through, remove any tool messages that occur before a non-tool message
                if token_overage == 0:
                    for i, message in enumerate(history):
                        if message.get("role") != "tool":
                            history = history[i:]
                            break

                # the token limit was reached, but continue to count the token overage
                token_overage += formatted_messages_token_count

        # while loop will now check for next batch of messages

    # We need to re-order the messages so that any messages that were made between when the assistant called the tool,
    # and when the tool call returned are placed *after* the tool call message with the result of the tool call.
    # This prevents an error where if the user sends a message while the assistant is waiting for a tool call to return,
    # the OpenAI API would error with: "An assistant message with 'tool_calls' must be followed by tool messages responding to each 'tool_call_id'"
    reordered_history = []
    i = 0
    while i < len(history):
        current_message = history[i]
        reordered_history.append(current_message)
        # If this is an assistant message with tool calls
        if current_message.get("role") == "assistant" and current_message.get("tool_calls"):
            tool_call_ids = {tc["id"] for tc in current_message.get("tool_calls", [])}
            intercepted_user_messages = []
            j = i + 1
            # Look ahead for corresponding tool messages or user messages
            while j < len(history):
                next_message = history[j]
                if next_message.get("role") == "tool" and next_message.get("tool_call_id") in tool_call_ids:
                    # Found the matching tool response
                    reordered_history.append(next_message)
                    tool_call_ids.remove(next_message.get("tool_call_id"))
                    j += 1
                    # Once we've found all tool responses, add the intercepted user messages
                    if not tool_call_ids:
                        reordered_history.extend(intercepted_user_messages)
                        i = j - 1  # Set i to the last processed index
                        break
                elif next_message.get("role") == "user":
                    # Store user messages that appear between tool call and response
                    intercepted_user_messages.append(next_message)
                    j += 1
                else:
                    break
        i += 1

    # return the formatted messages
    return GetHistoryMessagesResult(
        messages=reordered_history if reordered_history else history,
        token_count=token_count,
        token_overage=token_overage,
    )
