import logging

from chat_driver import ChatDriver, ChatDriverConfig
from chat_driver.in_memory_message_history_provider import InMemoryMessageHistoryProvider
from form_filler_skill.message import Conversation, ConversationMessageType
from openai import AsyncAzureOpenAI, AsyncOpenAI

logger = logging.getLogger(__name__)

AGENDA_ERROR_CORRECTION_SYSTEM_TEMPLATE = """You are a helpful, thoughtful, and meticulous assistant.
You are conducting a conversation with a user. You tried to update the agenda, but the update was invalid.

You will be provided the history of your conversation with the user, your previous attempt(s) at updating the agenda, and the error message(s) that resulted from your attempt(s).
Your task is to correct the update so that it is valid.

Your changes should be as minimal as possible - you are focused on fixing the error(s) that caused the update to be invalid.

Note that if the resource allocation is invalid, you must follow these rules:

1. You should not change the description of the first item (since it has already been executed), but you can change its resource allocation.
2. For all other items, you can combine or split them, or assign them fewer or more resources, but the content they cover collectively should not change (i.e. don't eliminate or add new topics).
For example, the invalid attempt was "item 1 = ask for date of birth (1 turn), item 2 = ask for phone number (1 turn), item 3 = ask for phone type (1 turn), item 4 = explore treatment history (6 turns)", and the error says you need to correct the total resource allocation to 7 turns. A bad solution is "item 1 = ask for date of birth (1 turn), item 2 = explore treatment history (6 turns)" because it eliminates the phone number and phone type topics. A good solution is "item 1 = ask for date of birth (2 turns), item 2 = ask for phone number, phone type, and treatment history (2 turns), item 3 = explore treatment history (3 turns)."
"""


async def fix_agenda_error(
    openai_client: AsyncOpenAI | AsyncAzureOpenAI,
    previous_attempts: str,
    conversation: Conversation,
):
    history = InMemoryMessageHistoryProvider()

    history.append_system_message(AGENDA_ERROR_CORRECTION_SYSTEM_TEMPLATE)
    history.append_user_message(
        (
            "Conversation history:\n"
            "{{ conversation_history }}\n\n"
            "Previous attempts to update the agenda:\n"
            "{{ previous_attempts }}"
        ),
        {
            "conversation_history": str(conversation.exclude([ConversationMessageType.REASONING])),
            "previous_attempts": previous_attempts,
        },
    )

    config = ChatDriverConfig(
        openai_client=openai_client,
        model="gpt-3.5-turbo",
        message_provider=history,
    )

    chat_driver = ChatDriver(config)
    return await chat_driver.respond()
