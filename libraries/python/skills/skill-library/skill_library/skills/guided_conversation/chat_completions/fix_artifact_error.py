from typing import Any

from openai_client import (
    CompletionError,
    add_serializable_data,
    create_system_message,
    create_user_message,
    make_completion_args_serializable,
    message_from_completion,
    validate_completion,
)
from skill_library.skills.guided_conversation.artifact_helpers import UpdateAttempt, get_schema_for_prompt
from skill_library.skills.guided_conversation.message import Conversation, ConversationMessageType
from skill_library.types import LanguageModel

from ..logging import logger

ARTIFACT_ERROR_CORRECTION_SYSTEM_TEMPLATE = """
You are a helpful, thoughtful, and meticulous assistant.

You are conducting a conversation with a user. Your goal is to complete an artifact as thoroughly as possible by the end of the conversation.

You have tried to update a field in the artifact, but the value you provided did not adhere to the constraints of the field as specified in the artifact schema.

You will be provided the history of your conversation with the user, the schema for the field, your previous attempt(s) at updating the field, and the error message(s) that resulted from your attempt(s).

Your task is to return the best possible action to take next:

1. UPDATE_FIELD(value)
- You should pick this action if you have a valid value to submit for the field in question. Replace "value" with the correct value.

2. RESUME_CONVERSATION
- You should pick this action if: (a) you do NOT have a valid value to submit for the field in question, and (b) you need to ask the user for more information in order to obtain a valid value. For example, if the user stated that their date of birth is June 2000, but the artifact field asks for the date of birth in the format "YYYY-MM-DD", you should resume the conversation and ask the user for the day.

Return only the action, either UPDATE_ARTIFACT(value) or RESUME_CONVERSATION, as your response. If you selected, UPDATE_ARTIFACT, make sure to replace "value" with the correct value.
""".replace("\n\n\n", "\n\n").strip()


async def generate_artifact_field_update_error_fix(
    language_model: LanguageModel,
    original_schema: dict[str, Any],
    field_name: str,
    field_value: Any,
    conversation: Conversation,
    previous_attempts: list["UpdateAttempt"],
) -> Any:
    previous_attempts_string = "\n".join([
        f"Attempt: {attempt.field_value}\nError: {attempt.error}" for attempt in previous_attempts
    ])

    # Use the language model to generate a fix for the artifact field update
    # error.

    completion_args = {
        "model": "gpt-3.5-turbo",
        "messages": [
            create_system_message(ARTIFACT_ERROR_CORRECTION_SYSTEM_TEMPLATE),
            create_user_message(
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
                    "artifact_schema": get_schema_for_prompt(original_schema, filter_one_field=field_name),
                    "field_name": field_name,
                    "previous_attempts": previous_attempts_string,
                },
            ),
        ],
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
        message = message_from_completion(completion)
        if message is None:
            raise ValueError("Failed to fix the artifact error due to an invalid response from the LLM.")

        if message.content not in ["UPDATE_ARTIFACT", "RESUME_CONVERSATION"]:
            raise ValueError(f"Failed to fix the artifact error due to an invalid response from the LLM: {message}")

        # TODO: This doesn't seem like the right thing to return.
        if message.content == "RESUME_CONVERSATION":
            return None

        if message.content.startswith("UPDATE_ARTIFACT("):
            field_value = message.content.split("(")[1].split(")")[0]
            return field_value

        raise ValueError(f"Failed to fix the artifact error due to an invalid response from the LLM: {message}")
