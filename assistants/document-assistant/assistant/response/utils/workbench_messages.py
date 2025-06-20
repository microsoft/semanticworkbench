import logging
from copy import deepcopy

from openai.types.chat import (
    ChatCompletionContentPartImageParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionToolParam,
    ChatCompletionUserMessageParam,
)
from openai.types.chat.chat_completion_content_part_image_param import ImageURL
from openai_client.tokens import num_tokens_from_tools_and_messages
from semantic_workbench_api_model import workbench_model
from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    ConversationParticipant,
    MessageType,
)
from semantic_workbench_assistant.assistant_app import (
    ConversationContext,
)

from assistant.filesystem import AttachmentsExtension
from assistant.response.utils.formatting_utils import format_message
from assistant.response.utils.message_utils import (
    conversation_message_to_assistant_message,
    conversation_message_to_tool_message,
    conversation_message_to_user_message,
)

logger = logging.getLogger(__name__)


async def _conversation_message_to_chat_message_params(
    context: ConversationContext,
    message: ConversationMessage,
    participants: list[ConversationParticipant],
) -> list[ChatCompletionMessageParam]:
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
        user_message_text = format_message(message, participants)
        # Iterate over the attachments associated with this message and append them at the end of the message.
        image_contents = []
        attachment_contents = []
        for filename in message.filenames:
            attachment_content = message.metadata.get("filename_to_content", {}).get(filename, "")
            if attachment_content:
                if attachment_content.startswith("data:image/"):
                    image_contents.append(
                        ChatCompletionContentPartImageParam(
                            type="image_url",
                            image_url=ImageURL(url=attachment_content, detail="high"),
                        )
                    )
                else:
                    attachment_contents.append(
                        ChatCompletionContentPartTextParam(
                            type="text",
                            text=f'<file filename="{filename}">\n{attachment_content}\n</file>',
                        )
                    )

        chat_message_params.append(
            ChatCompletionUserMessageParam(
                role="user",
                content=[
                    ChatCompletionContentPartTextParam(
                        type="text",
                        text=user_message_text,
                    )
                ]
                + attachment_contents
                + image_contents,
            )
        )
    return chat_message_params


async def get_workbench_messages(
    context: ConversationContext, attachments_extension: AttachmentsExtension
) -> workbench_model.ConversationMessageList:
    history = workbench_model.ConversationMessageList(messages=[])
    before_message_id = None
    while True:
        messages_response = await context.get_messages(
            limit=100, before=before_message_id, message_types=[MessageType.chat, MessageType.note, MessageType.log]
        )
        messages_list = messages_response.messages
        history.messages = messages_list + history.messages
        if not messages_list or messages_list.count == 0:
            break
        before_message_id = messages_list[0].id

    # Add mapping of filename to content to the metadata of each message
    for message in history.messages:
        if message.filenames:
            filenames = message.filenames
            message.metadata["filename_to_content"] = {}
            for filename in filenames:
                attachment_content = await attachments_extension.get_attachment(context, filename)
                if attachment_content:
                    message.metadata["filename_to_content"][filename] = attachment_content

    return history


async def workbench_message_to_oai_messages(
    context: ConversationContext,
    messages: workbench_model.ConversationMessageList,
    participants_response: workbench_model.ConversationParticipantList,
) -> list[ChatCompletionMessageParam]:
    participants = participants_response.participants

    oai_messages = []
    for message in messages.messages:
        oai_messages.extend(await _conversation_message_to_chat_message_params(context, message, participants))

    # Post processing to ensure an assistant message with a tool call is always followed by the corresponding tool message.
    # If there is a tool message without a corresponding assistant message, do not include it.
    # If the tool message does not immediately follow the assistant, move it so that it does.
    # First, identify all assistant messages with tool calls and their corresponding tool messages
    assistant_tool_calls: dict[str, int] = {}  # tool_call_id -> assistant message index
    tool_messages: dict[str, tuple[int, ChatCompletionToolMessageParam]] = {}  # tool_call_id -> (index, message)
    for i, msg in enumerate(oai_messages):
        if msg["role"] == "assistant" and "tool_calls" in msg:
            for tool_call in msg["tool_calls"]:
                assistant_tool_calls[tool_call["id"]] = i
        elif msg["role"] == "tool":
            tool_messages[msg["tool_call_id"]] = (i, msg)

    # Build the final message list with proper ordering
    final_messages: list[ChatCompletionMessageParam] = []
    processed_tool_messages: set[str] = set()
    i = 0
    while i < len(oai_messages):
        msg = oai_messages[i]

        if msg["role"] == "tool":
            # Skip tool messages here - they'll be added after their corresponding assistant message
            i += 1
            continue

        # Add the current message
        final_messages.append(msg)

        # If this is an assistant message with tool calls, add corresponding tool messages immediately after
        if msg["role"] == "assistant" and "tool_calls" in msg:
            for tool_call in msg["tool_calls"]:
                tool_call_id = tool_call["id"]
                if tool_call_id in tool_messages:
                    _, tool_msg = tool_messages[tool_call_id]
                    final_messages.append(tool_msg)
                    processed_tool_messages.add(tool_call_id)
        i += 1

    return final_messages


async def compute_tokens_from_workbench_messages(
    context: ConversationContext,
    messages: workbench_model.ConversationMessageList,
    tools: list[ChatCompletionToolParam],
    participants_response: workbench_model.ConversationParticipantList,
    messages_for_removal: list[int] = [],
    token_model: str = "gpt-4o",
) -> int:
    # Remove the messages that are marked for removal
    new_messages = []
    for i in range(len(messages.messages)):
        if i not in messages_for_removal:
            new_messages.append(messages.messages[i])
    messages = deepcopy(messages)
    messages.messages = new_messages
    oai_messages = await workbench_message_to_oai_messages(context, messages, participants_response)
    current_tokens = num_tokens_from_tools_and_messages(tools, oai_messages, token_model)
    return current_tokens
