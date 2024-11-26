import logging
from typing import Any

from form_filler_skill.guided_conversation.artifact_helpers import get_schema_for_prompt
from form_filler_skill.guided_conversation.definition import GCDefinition
from openai_client import (
    CompletionError,
    add_serializable_data,
    create_system_message,
    make_completion_args_serializable,
    message_content_from_completion,
    validate_completion,
)
from pydantic import BaseModel
from skill_library.types import LanguageModel

from ..message import Conversation

logger = logging.getLogger(__name__)

USER_MESSAGE_TEMPLATE = """You are a helpful, thoughtful, and meticulous assistant. You are conducting a conversation with a user. Your goal is to complete an artifact as thoroughly as possible by the end of the conversation, and to ensure a smooth experience for the user.

This is the schema of the artifact you are completing:
{{ artifact_schema }}{% if context %}

Here is some additional context about the conversation:
{{ context }}{% endif %}

Throughout the conversation, you must abide by these rules:
{{ rules }}{% if current_state_description %}

Here's a description of the conversation flow:
{{ current_state_description }}

Follow this description, and exercise good judgment about when it is appropriate to deviate.{% endif %}

You will be provided the history of your conversation with the user up until now and the current state of the artifact. Note that if the value for a field in the artifact is 'Unanswered', it means that the field has not been completed.

Your job is to respond to the user if they ask a question or make a statement that you need to respond to or if you need to follow-up with the user because the information they provided is incomplete, invalid, ambiguous, or in some way insufficient to complete the artifact.

For example, if the artifact schema indicates that the "date of birth" field must be in the format "YYYY-MM-DD", but the user has only provided the month and year, you should send a message to the user asking for the day. Likewise, if the user claims that their date of birth is February 30, you should send a message to the user asking for a valid date. If the artifact schema is open-ended (e.g. it asks you to rate how pressing the user's issue is, without specifying rules for doing so), use your best judgment to determine whether you have enough information or you need to continue
probing the user. It's important to be thorough, but also to avoid asking the user for unnecessary information.
"""


class ArtifactUpdate(BaseModel):
    field: str
    value: Any


class ArtifactUpdates(BaseModel):
    updates: list[ArtifactUpdate]


class UpdateAttempt(BaseModel):
    field_value: str
    error: str


async def generate_message(
    language_model: LanguageModel,
    definition: GCDefinition,
    artifact: BaseModel | None,
    conversation: Conversation,
    max_retries: int = 2,
) -> str:
    # Use the language model to generate a response to the user.

    completion_args = {
        "model": "gpt-4o",
        "messages": [
            create_system_message(
                USER_MESSAGE_TEMPLATE,
                {
                    "artifact_schema": get_schema_for_prompt(definition.artifact_schema),
                    "context": definition.conversation_context,
                    "rules": definition.rules,
                    "current_state_description": definition.conversation_flow,
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
        return message_content_from_completion(completion)
