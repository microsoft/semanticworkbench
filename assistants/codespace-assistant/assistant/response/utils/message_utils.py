import json
import logging
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

from ...config import AssistantConfigModel
from .formatting_utils import format_message

logger = logging.getLogger(__name__)


def build_system_message_content(
    config: AssistantConfigModel,
    context: ConversationContext,
    participants: list[ConversationParticipant],
    silence_token: str,
) -> str:
    """
    Construct the system message content with tool descriptions and instructions.
    """

    system_message_content = f'{config.instruction_prompt}\n\nYour name is "{context.assistant.name}".\n'

    if len(participants) > 2:
        participant_names = ", ".join([
            f'"{participant.name}"' for participant in participants if participant.id != context.assistant.id
        ])
        system_message_content += (
            "\n\n"
            f"There are {len(participants)} participants in the conversation, "
            f"including you as the assistant and the following users: {participant_names}."
            "\n\nYou do not need to respond to every message. Do not respond if the last thing said was a closing "
            f'statement such as "bye" or "goodbye", or just a general acknowledgement like "ok" or "thanks". Do not '
            f'respond as another user in the conversation, only as "{context.assistant.name}". '
            "Sometimes the other users need to talk amongst themselves and that is okay. If the conversation seems to "
            "be directed at you or the general audience, go ahead and respond."
            f'\n\nSay "{silence_token}" to skip your turn.'
        )

    system_message_content += f"\n\n{config.guardrails_prompt}"

    return system_message_content


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
) -> list[ChatCompletionMessageParam]:
    """
    Get all messages in the conversation, formatted for use in a completion.
    """

    # each call to get_messages will return a maximum of 100 messages
    # so we need to loop until all messages are retrieved
    # if token_limit is provided, we will stop when the token limit is reached

    history = []
    token_count = 0
    before_message_id = None

    while True:
        # get the next batch of messages, including chat and tool result messages
        messages_response = await context.get_messages(
            limit=100, before=before_message_id, message_types=[MessageType.chat, MessageType.note]
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
            token_count += openai_client.num_tokens_from_messages(formatted_message_list, model=model)

            # if a token limit is provided and the token count exceeds the limit, break the loop
            if token_limit and token_count > token_limit:
                break

            # insert the formatted messages into the beginning of the history list
            history = formatted_message_list + history

    # return the formatted messages
    return history
