import logging
from typing import cast

from openai_client import (
    CompletionError,
    add_serializable_data,
    create_system_message,
    create_user_message,
    make_completion_args_serializable,
    validate_completion,
)
from skill_library.types import LanguageModel

from ..agenda import Agenda
from ..message import Conversation, ConversationMessageType

logger = logging.getLogger(__name__)

AGENDA_ERROR_CORRECTION_SYSTEM_TEMPLATE = """
You are a helpful, thoughtful, and meticulous assistant.
You are conducting a conversation with a user. You tried to update the agenda, but the update was invalid.

You will be provided the history of your conversation with the user, your previous attempt(s) at updating the agenda, and the error message(s) that resulted from your attempt(s).
Your task is to correct the update so that it is valid.

Your changes should be as minimal as possible - you are focused on fixing the error(s) that caused the update to be invalid.

Note that if the resource allocation is invalid, you must follow these rules:

1. You should not change the description of the first item (since it has already been executed), but you can change its resource allocation.
2. For all other items, you can combine or split them, or assign them fewer or more resources, but the content they cover collectively should not change (i.e. don't eliminate or add new topics).
For example, the invalid attempt was "item 1 = ask for date of birth (1 turn), item 2 = ask for phone number (1 turn), item 3 = ask for phone type (1 turn), item 4 = explore treatment history (6 turns)", and the error says you need to correct the total resource allocation to 7 turns. A bad solution is "item 1 = ask for date of birth (1 turn), item 2 = explore treatment history (6 turns)" because it eliminates the phone number and phone type topics. A good solution is "item 1 = ask for date of birth (2 turns), item 2 = ask for phone number, phone type, and treatment history (2 turns), item 3 = explore treatment history (3 turns)."
""".replace("\n\n\n", "\n\n").strip()


async def fix_agenda_error(
    language_model: LanguageModel,
    previous_attempts: str,
    conversation: Conversation,
) -> Agenda:
    completion_args = {
        "model": "gpt-3.5-turbo",
        "messages": [
            create_system_message(AGENDA_ERROR_CORRECTION_SYSTEM_TEMPLATE),
            create_user_message(
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
            ),
        ],
        "response_format": Agenda,
    }

    metadata = {}
    logger.debug("Completion call.", extra=add_serializable_data(make_completion_args_serializable(completion_args)))
    metadata["completion_args"] = make_completion_args_serializable(completion_args)
    try:
        completion = await language_model.beta.chat.completions.parse(
            **completion_args,
        )
        validate_completion(completion)
        logger.debug("Completion response.", extra=add_serializable_data({"completion": completion.model_dump()}))
        metadata["completion"] = completion.model_dump()
    except CompletionError as e:
        completion_error = CompletionError(e)
        metadata["completion_error"] = completion_error.message
        logger.error(
            e.message, extra=add_serializable_data({"completion_error": completion_error.body, "metadata": metadata})
        )
        raise completion_error from e
    else:
        agenda = cast(Agenda, completion.choices[0].message.parsed)
        return agenda
