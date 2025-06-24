"""Utility functions for retrieving message history using chat_context_toolkit."""

import datetime
import logging
import uuid
from typing import Protocol, Sequence

from chat_context_toolkit.archive import MessageProtocol as ArchiveMessageProtocol
from chat_context_toolkit.archive import MessageProvider as ArchiveMessageProvider
from chat_context_toolkit.history import (
    HistoryMessage,
    HistoryMessageProtocol,
    HistoryMessageProvider,
    OpenAIHistoryMessageParam,
)
from chat_context_toolkit.history.tool_abbreviations import ToolAbbreviations, abbreviate_openai_tool_message
from openai.types.chat import ChatCompletionContentPartTextParam, ChatCompletionUserMessageParam
from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    MessageType,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from ._message import conversation_message_to_chat_message_param

logger = logging.getLogger(__name__)


class HistoryMessageWithAbbreviation(HistoryMessage):
    """
    A HistoryMessageProtocol implementation that includes:
    - abbreviations for tool messages
    - abbreviations for assistant messages with tool calls
    - abbreviations for messages with attachment content-parts
    """

    def __init__(
        self,
        id: str,
        timestamp: datetime.datetime,
        openai_message: OpenAIHistoryMessageParam,
        tool_abbreviations: ToolAbbreviations,
        tool_name_for_tool_message: str | None = None,
    ) -> None:
        super().__init__(id=id, openai_message=openai_message, abbreviator=self.abbreviator)
        self._timestamp = timestamp
        self._tool_abbreviations = tool_abbreviations
        self._tool_name_for_tool_message = tool_name_for_tool_message

    @property
    def timestamp(self) -> datetime.datetime:
        return self._timestamp

    def abbreviator(self) -> OpenAIHistoryMessageParam | None:
        match self.openai_message:
            case {"role": "user"}:
                return abbreviate_attachment_content_parts(openai_message=self.openai_message)
            case {"role": "tool"} | {"role": "assistant"}:
                return abbreviate_openai_tool_message(
                    openai_message=self.openai_message,
                    tool_abbreviations=self._tool_abbreviations,
                    tool_name_for_tool_message=self._tool_name_for_tool_message,
                )

            case _:
                # for all other messages, we return the original message
                return self.openai_message


def abbreviate_attachment_content_parts(
    openai_message: ChatCompletionUserMessageParam,
) -> OpenAIHistoryMessageParam:
    """
    Abbreviate the user message if it contains attachment content parts.
    """
    if "content" not in openai_message:
        return openai_message

    content_parts = openai_message["content"]
    if not isinstance(content_parts, list):
        return openai_message

    # the first content-part is always the text content, so we can keep it as is
    abbreviated_content_parts = [content_parts[0]]
    for part in content_parts[1:]:
        match part:
            case {"type": "text"}:
                # truncate the attachment content parts - ie. the one's that don't say "Attachment: <filename>"
                if part["text"].startswith("Attachment: "):
                    # Keep the attachment content parts as is
                    abbreviated_content_parts.append(part)
                    continue

                abbreviated_content_parts.append(
                    ChatCompletionContentPartTextParam(
                        type="text",
                        text="The content of this attachment has been removed due to token limits. Please use view to retrieve the most recent content if you need it.",
                    )
                )

            case {"type": "image_url"}:
                abbreviated_content_parts.append(
                    ChatCompletionContentPartTextParam(
                        type="text",
                        text="The content of this attachment has been removed due to token limits. Please use view to retrieve the most recent content if you need it.",
                    )
                )

            case _:
                abbreviated_content_parts.append(part)

    return {**openai_message, "content": abbreviated_content_parts}


class CompositeMessageProvider(HistoryMessageProvider, ArchiveMessageProvider, Protocol):
    """
    A composite message provider that combines both history and archive message providers.
    """

    ...


class CompositeMessageProtocol(HistoryMessageProtocol, ArchiveMessageProtocol, Protocol):
    """
    A composite message protocol that combines both history and archive message protocols.
    """

    ...


def chat_context_toolkit_message_provider_for(
    context: ConversationContext, tool_abbreviations: ToolAbbreviations
) -> CompositeMessageProvider:
    """
    Create a composite message provider for the given workbench conversation context.
    """

    async def provider(after_id: str | None = None) -> Sequence[CompositeMessageProtocol]:
        history = await _get_history_manager_messages(context, tool_abbreviations=tool_abbreviations, after_id=after_id)

        return history

    return provider


async def _get_history_manager_messages(
    context: ConversationContext, tool_abbreviations: ToolAbbreviations, after_id: str | None = None
) -> list[HistoryMessageWithAbbreviation]:
    """
    Get all messages in the conversation, formatted for the chat_context_toolkit.
    """

    participants_response = await context.get_participants(include_inactive=True)
    participants = participants_response.participants

    history: list[HistoryMessageWithAbbreviation] = []

    batch_size = 100
    before_message_id = None

    # each call to get_messages will return a maximum of `batch_size` messages
    # so we need to loop until all messages are retrieved
    while True:
        # get the next batch of messages, including chat and tool result messages
        messages_response = await context.get_messages(
            limit=batch_size,
            before=before_message_id,
            message_types=[MessageType.chat, MessageType.note],
            after=uuid.UUID(after_id) if after_id else None,
        )
        messages_list = messages_response.messages

        if not messages_list:
            # if there are no more messages, we are done
            break

        # set the before_message_id for the next batch of messages
        before_message_id = messages_list[0].id

        batch: list[HistoryMessageWithAbbreviation] = []
        for message in messages_list:
            # format the message
            formatted_message = await conversation_message_to_chat_message_param(context, message, participants)

            if not formatted_message:
                # if the message could not be formatted, skip it
                logger.warning("message %s could not be formatted, skipping.", message.id)
                continue

            # prepend the formatted messages to the history list
            batch.append(
                HistoryMessageWithAbbreviation(
                    id=str(message.id),
                    openai_message=formatted_message,
                    tool_abbreviations=tool_abbreviations,
                    tool_name_for_tool_message=tool_name_for_tool_message(message),
                    timestamp=message.timestamp,
                )
            )

        # add the formatted messages to the history
        history = batch + history

        if len(messages_list) < batch_size:
            # if we received less than `batch_size` messages, we have reached the end of the conversation.
            # exit early to avoid another unnecessary message query.
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
