import logging
from typing import Callable

import openai_client
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionSystemMessageParam
from semantic_workbench_api_model.workbench_model import (
    #    AssistantStateEvent,
    ConversationMessage,
    ConversationParticipant,
    MessageType,
    NewConversationMessage,
    #    ParticipantRole,
)
from semantic_workbench_assistant.assistant_app import (
    ConversationContext,
    #    storage_directory_for_context,
)

from ..agents.attachment_agent import AttachmentAgent
from ..config import AssistantConfigModel

logger = logging.getLogger(__name__)

#
# region Agent
#


class DocumentAgent:
    """
    An agent for working on document content: creation, editing, translation, etc.
    """

    def __init__(self) -> None:
        self._commands = [self.draft_outline]

    @property
    def commands(self) -> list[Callable]:
        return self._commands

    async def receive_command(
        self, config: AssistantConfigModel, context: ConversationContext, message: ConversationMessage
    ) -> None:
        # check if available. If not, ignore for now.
        command_found = False
        for command in self.commands:
            if command.__name__ == message.command_name:
                print(f"Found command {message.command_name}")
                command_found = True
                await command(config, context, message)  # TO DO, handle commands with args
                break
        if not command_found:
            print(f"Could not find command {message.command_name}")

    async def draft_outline(
        self, config: AssistantConfigModel, context: ConversationContext, message: ConversationMessage
    ) -> None:
        chat_completion_messages: list[ChatCompletionMessageParam] = []

        _add_main_system_message(chat_completion_messages, draft_outline_main_system_message)

        conversation = await context.get_messages(before=message.id)
        conversation.messages.append(message)
        participants_list = await context.get_participants(include_inactive=True)
        _add_chat_history_system_message(
            chat_completion_messages, conversation.messages, participants_list.participants
        )

        attachment_messages = AttachmentAgent.generate_attachment_messages(context)
        _add_attachments_system_message(chat_completion_messages, config, attachment_messages)

        # make completion call to openai
        async with openai_client.create_client(config.service_config) as client:
            try:
                completion_args = {
                    "messages": chat_completion_messages,
                    "model": config.request_config.openai_model,
                    "response_format": {"type": "text"},
                }
                completion = await client.chat.completions.create(**completion_args)
                content = completion.choices[0].message.content
            except Exception as e:
                logger.exception(f"exception occurred calling openai chat completion: {e}")

        # send the response to the conversation
        message_type = MessageType.chat
        if message.message_type == MessageType.command:
            message_type = MessageType.command_response

        await context.send_messages(
            NewConversationMessage(
                content=content or "[no response from openai]",
                message_type=message_type,
                # metadata=metadata, TO DO
            )
        )


# endregion

#
# region Message Helpers
#


def _add_main_system_message(chat_completion_messages: list[ChatCompletionMessageParam], prompt: str) -> None:
    message: ChatCompletionSystemMessageParam = {"role": "system", "content": prompt}
    chat_completion_messages.append(message)


def _add_chat_history_system_message(
    chat_completion_messages: list[ChatCompletionMessageParam],
    conversation_messages: list[ConversationMessage],
    participants: list[ConversationParticipant],
) -> None:
    chat_history_message_list = []
    for conversation_message in conversation_messages:
        chat_history_message = _format_message(conversation_message, participants)
        chat_history_message_list.append(chat_history_message)
    chat_history_str = " ".join(chat_history_message_list)

    message: ChatCompletionSystemMessageParam = {
        "role": "system",
        "content": f"<CHAT_HISTORY>{chat_history_str}</CHAT_HISTORY>",
    }
    chat_completion_messages.append(message)


def _add_attachments_system_message(
    chat_completion_messages: list[ChatCompletionMessageParam],
    config: AssistantConfigModel,
    attachment_messages: list[ChatCompletionMessageParam],
) -> None:
    if len(attachment_messages) > 0:
        chat_completion_messages.append({
            "role": "system",
            "content": config.agents_config.attachment_agent.context_description,
        })
        chat_completion_messages.extend(attachment_messages)


# borrowed from Prospector chat.py
def _format_message(message: ConversationMessage, participants: list[ConversationParticipant]) -> str:
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


draft_outline_main_system_message = (
    "Generate an outline for the document, including title. The outline should include the key points that will"
    " be covered in the document. Consider the attachments, the rationale for why they were uploaded, and the"
    " conversation that has taken place. The outline should be a hierarchical structure with multiple levels of"
    " detail, and it should be clear and easy to understand. The outline should be generated in a way that is"
    " consistent with the document that will be generated from it."
)
# ("You are an AI assistant that helps draft outlines for a future flushed-out document."
# " You use information from a chat history between a user and an assistant, a prior version of a draft"
# " outline if it exists, as well as any other attachments provided by the user to inform a newly revised "
# "outline draft. Provide ONLY any outline. Provide no further instructions to the user.")
