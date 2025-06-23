import json
import logging
from typing import Any

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionContentPartImageParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionMessageToolCallParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)
from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    ConversationParticipant,
    MessageType,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from ..attachments import get_attachments

logger = logging.getLogger(__name__)


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


async def conversation_message_to_user_message(
    context: ConversationContext,
    message: ConversationMessage,
    participants: list[ConversationParticipant],
) -> ChatCompletionUserMessageParam:
    """
    Convert a conversation message to a user message. For messages with attachments, the attachments
    are included as content parts.
    """

    # if the message has no attachments, just return a user message with the formatted content
    if not message.filenames:
        return ChatCompletionUserMessageParam(
            role="user",
            content=format_message(message, participants),
        )

    # for messages with attachments, we need to create a user message with content parts

    # include the formatted message from the user
    content_parts: list[ChatCompletionContentPartTextParam | ChatCompletionContentPartImageParam] = [
        ChatCompletionContentPartTextParam(
            type="text",
            text=format_message(message, participants),
        )
    ]

    # additionally, include any attachments as content parts
    for filename in message.filenames:
        attachments = await get_attachments(context=context, include_filenames=[filename], exclude_filenames=[])

        attachment_filename = f"/attachments/{filename}"

        content_parts.append(
            ChatCompletionContentPartTextParam(
                type="text",
                text=f"Attachment: {attachment_filename}",
            )
        )

        if not attachments:
            content_parts.append(
                ChatCompletionContentPartTextParam(
                    type="text",
                    text="File has been deleted",
                )
            )
            continue

        attachment = attachments[0]

        if attachment.error:
            content_parts.append(
                ChatCompletionContentPartTextParam(
                    type="text",
                    text=f"Attachment has an error: {attachment.error}",
                )
            )
            continue

        if attachment.content.startswith("data:image/"):
            content_parts.append(
                ChatCompletionContentPartImageParam(
                    type="image_url",
                    image_url={
                        "url": attachment.content,
                    },
                )
            )
            continue

        content_parts.append(
            ChatCompletionContentPartTextParam(
                type="text",
                text=attachment.content or "(attachment has no content)",
            )
        )

    return ChatCompletionUserMessageParam(
        role="user",
        content=content_parts,
    )


async def conversation_message_to_chat_message_param(
    context: ConversationContext, message: ConversationMessage, participants: list[ConversationParticipant]
) -> ChatCompletionUserMessageParam | ChatCompletionAssistantMessageParam | ChatCompletionToolMessageParam | None:
    """
    Convert a conversation message to a list of chat message parameters.
    """

    # add the message to list, treating messages from a source other than this assistant as a user message
    if message.message_type == MessageType.note:
        # we are stuffing tool messages into the note message type, so we need to check for that
        tool_message = conversation_message_to_tool_message(message)
        if tool_message is None:
            logger.warning(f"Failed to convert tool message to completion message: {message}")
            return None

        return tool_message

    if message.sender.participant_id == context.assistant.id:
        # add the assistant message to the completion messages
        assistant_message = conversation_message_to_assistant_message(message, participants)
        return assistant_message

    # add the user message to the completion messages
    user_message = await conversation_message_to_user_message(
        context=context, message=message, participants=participants
    )

    return user_message


def format_message(message: ConversationMessage, participants: list[ConversationParticipant]) -> str:
    """
    Format a conversation message for display.
    """
    conversation_participant = next(
        (participant for participant in participants if participant.id == message.sender.participant_id),
        None,
    )
    participant_name = conversation_participant.name if conversation_participant else "unknown"
    message_datetime = message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    return f"[{participant_name} - {message_datetime}]: {message.content}"
