import logging

from events import BaseEvent
from form_filler_skill.message import Conversation, ConversationMessageType
from openai import AsyncAzureOpenAI, AsyncOpenAI
from openai_client.chat_driver import ChatDriver, ChatDriverConfig, InMemoryMessageHistoryProvider

logger = logging.getLogger(__name__)

ARTIFACT_ERROR_CORRECTION_SYSTEM_TEMPLATE = """You are a helpful, thoughtful, and meticulous assistant.

You are conducting a conversation with a user. Your goal is to complete an artifact as thoroughly as possible by the end of the conversation.

You have tried to update a field in the artifact, but the value you provided did not adhere to the constraints of the field as specified in the artifact schema.

You will be provided the history of your conversation with the user, the schema for the field, your previous attempt(s) at updating the field, and the error message(s) that resulted from your attempt(s).

Your task is to return the best possible action to take next:

1. UPDATE_FIELD(value)
- You should pick this action if you have a valid value to submit for the field in question. Replace "value" with the correct value.

2. RESUME_CONVERSATION
- You should pick this action if: (a) you do NOT have a valid value to submit for the field in question, and (b) you need to ask the user for more information in order to obtain a valid value. For example, if the user stated that their date of birth is June 2000, but the artifact field asks for the date of birth in the format "YYYY-MM-DD", you should resume the conversation and ask the user for the day.

Return only the action, either UPDATE_ARTIFACT(value) or RESUME_CONVERSATION, as your response. If you selected, UPDATE_ARTIFACT, make sure to replace "value" with the correct value.
"""


async def fix_artifact_error(
    openai_client: AsyncOpenAI | AsyncAzureOpenAI,
    previous_attempts: str,
    artifact_schema: str,
    conversation: Conversation,
    field_name: str,
) -> BaseEvent:
    history = InMemoryMessageHistoryProvider()
    history.append_system_message(ARTIFACT_ERROR_CORRECTION_SYSTEM_TEMPLATE)
    history.append_user_message(
        (
            "Conversation history:\n"
            "{{ conversation_history }}\n\n"
            "Schema:\n"
            "{{ artifact_schema }}\n\n"
            'Previous attempts to update the field "{{ field_name }}" in the artifact:\n'
            "{{ previous_attempts }}"
        ),
        {
            "conversation_history": str(conversation.exclude([ConversationMessageType.REASONING])),
            "artifact_schema": artifact_schema,
            "field_name": field_name,
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
