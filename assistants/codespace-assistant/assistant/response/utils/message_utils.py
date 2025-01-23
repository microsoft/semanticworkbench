import json
import logging
import re
from typing import Any, Awaitable, Callable, Sequence

from assistant_extensions.ai_clients.model import CompletionMessage
from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    ConversationParticipant,
    MessageType,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant.config import AssistantConfigModel
from assistant.response.utils.formatting_utils import format_message

from ..providers import ResponseProvider
from .token_utils import num_tokens_from_messages

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


async def conversation_message_to_completion_messages(
    context: ConversationContext, message: ConversationMessage, participants: list[ConversationParticipant]
) -> list[CompletionMessage]:
    """
    Convert a conversation message to a list of completion messages.
    """

    # some messages may have multiple parts, such as a text message with an attachment
    completion_messages: list[CompletionMessage] = []

    # add the message to the completion messages, treating any message from a source other than the assistant
    # as a user message
    if message.message_type == MessageType.tool_result:
        tool_result = message.metadata.get("tool_result")
        if tool_result:
            completion_messages.append(
                CompletionMessage(
                    role="tool",
                    content=tool_result.get("content"),
                    tool_call_id=tool_result.get("tool_call_id"),
                    metadata=message.metadata,
                )
            )

    elif message.sender.participant_id == context.assistant.id:
        # get the tool calls from the message metadata
        tool_calls: list[dict[str, Any]] | None = None
        if message.metadata is not None and "tool_calls" in message.metadata:
            # FIXME: this is forcing the OpenAI format, but it should be more generic
            tool_calls = [
                {
                    "id": tool_call["id"],
                    "type": "function",
                    "function": {"name": tool_call["name"], "arguments": json.dumps(tool_call["arguments"])},
                }
                for tool_call in message.metadata["tool_calls"]
            ]

        completion_messages.append(
            CompletionMessage(
                role="assistant",
                content=format_message(message, participants),
                tool_calls=tool_calls,
                metadata=message.metadata,
            )
        )

    else:
        # add the user message to the completion messages
        completion_messages.append(
            CompletionMessage(
                role="user",
                content=format_message(message, participants),
                metadata=message.metadata,
            )
        )

        if message.filenames and len(message.filenames) > 0:
            # add a system message to indicate the attachments
            completion_messages.append(
                CompletionMessage(
                    role="system", content=f"Attachment(s): {', '.join(message.filenames)}", metadata=message.metadata
                )
            )

    return completion_messages


async def get_history_messages(
    response_provider: ResponseProvider,
    context: ConversationContext,
    participants: list[ConversationParticipant],
    converter: Callable[
        [ConversationContext, ConversationMessage, list[ConversationParticipant]],
        Awaitable[list[CompletionMessage]],
    ],
    model: str,
    token_limit: int | None = None,
) -> list[CompletionMessage]:
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
            limit=100, before=before_message_id, message_types=[MessageType.chat, MessageType.tool_result]
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
            formatted_message_list = await converter(context, message, participants)
            try:
                results = await num_tokens_from_messages(
                    context=context,
                    response_provider=response_provider,
                    messages=formatted_message_list,
                    model=model,
                    metadata={},
                    metadata_key="get_history_messages",
                )
                if results is not None:
                    token_count += results.count
            except Exception as e:
                logger.exception(f"exception occurred calculating token count: {e}")

            # if a token limit is provided and the token count exceeds the limit, break the loop
            if token_limit and token_count > token_limit:
                break

            # insert the formatted messages into the beginning of the history list
            history = formatted_message_list + history

    # return the formatted messages
    return history


def inject_attachments_inline(
    history_messages: list[CompletionMessage],
    attachment_messages: Sequence[CompletionMessage],
) -> list[CompletionMessage]:
    """
    Inject the attachment messages inline into the history messages.
    """

    # iterate over the history messages and for every message that contains an attachment,
    # find the related attachment message and replace the attachment message with the inline attachment content
    for index, history_message in enumerate(history_messages):
        # if the history message does not contain content, as a string value, skip
        content = history_message.content
        if not content or not isinstance(content, str):
            # TODO: handle list content, which may contain multiple parts including images
            continue

        # get the attachment filenames string from the history message content
        attachment_filenames_string = re.findall(r"Attachment\(s\): (.+)", content)

        # if the history message does not contain an attachment filenames string, skip
        if not attachment_filenames_string:
            continue

        # split the attachment filenames string into a list of attachment filenames
        attachment_filenames = [filename.strip() for filename in attachment_filenames_string[0].split(",")]

        # initialize a list to store the replacement messages
        replacement_messages = []

        # iterate over the attachment filenames and find the related attachment message
        for attachment_filename in attachment_filenames:
            # find the related attachment message
            attachment_message = next(
                (
                    attachment_message
                    for attachment_message in attachment_messages
                    if f"<ATTACHMENT><FILENAME>{attachment_filename}</FILENAME>" in str(attachment_message.content)
                ),
                None,
            )

            if attachment_message:
                # replace the attachment message with the inline attachment content
                replacement_messages.append(attachment_message)

        # if there are replacement messages, replace the history message with the replacement messages
        if len(replacement_messages) > 0:
            history_messages[index : index + 1] = replacement_messages

    return history_messages
