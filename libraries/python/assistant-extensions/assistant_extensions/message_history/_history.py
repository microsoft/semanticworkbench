"""Utility functions for retrieving message history using chat_context_toolkit."""

import logging
import uuid
from typing import Sequence

from chat_context_toolkit.history import HistoryMessageProtocol, HistoryMessageProvider
from chat_context_toolkit.history.tool_abbreviations import (
    HistoryMessageWithToolAbbreviation,
    ToolAbbreviations,
)
from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    MessageType,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from ._message import conversation_message_to_chat_message_params

logger = logging.getLogger(__name__)


def chat_context_toolkit_message_provider_for(
    context: ConversationContext, tool_abbreviations: ToolAbbreviations
) -> HistoryMessageProvider:
    """
    Create a history message provider for the given workbench conversation context.
    """

    async def provider(after_id: str | None) -> Sequence[HistoryMessageProtocol]:
        history = await _get_history_manager_messages(context, after_id=after_id, tool_abbreviations=tool_abbreviations)

        return history

    return provider


async def _get_history_manager_messages(
    context: ConversationContext, after_id: str | None, tool_abbreviations: ToolAbbreviations
) -> list[HistoryMessageWithToolAbbreviation]:
    """
    Get all messages in the conversation, formatted for the chat_context_toolkit.
    """

    participants_response = await context.get_participants(include_inactive=True)
    participants = participants_response.participants

    # each call to get_messages will return a maximum of 100 messages
    # so we need to loop until all messages are retrieved
    # if token_limit is provided, we will stop when the token limit is reached

    history: list[HistoryMessageWithToolAbbreviation] = []

    page_size = 100
    before_message_id = None

    while True:
        # get the next batch of messages, including chat and tool result messages
        messages_response = await context.get_messages(
            limit=page_size,
            before=before_message_id,
            message_types=[MessageType.chat, MessageType.note],
            after=uuid.UUID(after_id) if after_id else None,
        )
        messages_list = messages_response.messages

        # set the before_message_id for the next batch of messages
        before_message_id = messages_list[0].id

        page: list[HistoryMessageWithToolAbbreviation] = []
        for message in messages_list:
            # format the message
            formatted_message_list = await conversation_message_to_chat_message_params(context, message, participants)

            # prepend the formatted messages to the history list
            page.extend([
                HistoryMessageWithToolAbbreviation(
                    id=str(message.id),
                    openai_message=formatted_message,
                    tool_abbreviations=tool_abbreviations,
                    tool_name_for_tool_message=tool_name_for_tool_message(message),
                )
                for formatted_message in formatted_message_list
            ])

        # add the formatted messages to the history
        history = page + history

        if len(messages_list) < page_size:
            # if we received less than `page_size` messages, we have reached the end of the conversation
            break

    # return the formatted messages
    return history


def tool_name_for_tool_message(message: ConversationMessage) -> str:
    """
    Get the tool name for the given tool message.

    NOTE: This function assumes that the tool call metadata is structured in a specific way.
    """
    tool_calls = message.metadata.get("tool_calls")
    if not tool_calls or not isinstance(tool_calls, list) or len(tool_calls) == 0:
        return ""
    # Return the name of the first tool call
    # This assumes that the tool call metadata is structured as expected
    return tool_calls[0].get("name") or "<unknown>"
