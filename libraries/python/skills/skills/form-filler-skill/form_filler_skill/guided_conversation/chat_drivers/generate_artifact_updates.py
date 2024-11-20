import logging
from typing import Any, cast

from form_filler_skill.guided_conversation.definition import GCDefinition
from openai_client import (
    CompletionError,
    add_serializable_data,
    create_system_message,
    make_completion_args_serializable,
    validate_completion,
)
from pydantic import BaseModel
from skill_library.types import LanguageModel

from ..artifact import Artifact
from ..message import Conversation
from .fix_artifact_error import UpdateAttempt, generate_artifact_field_update_error_fix

logger = logging.getLogger(__name__)

UPDATE_ARTIFACT_TEMPLATE = """You are a helpful, thoughtful, and meticulous assistant. You are conducting a conversation with a user. Your goal is to complete an artifact as thoroughly as possible by the end of the conversation, and to ensure a smooth experience for the user.

This is the schema of the artifact you are completing:
{{ artifact_schema }}{% if context %}

Here is some additional context about the conversation:
{{ context }}{% endif %}

Throughout the conversation, you must abide by these rules:
{{ rules }}{% if current_state_description %}

Here's a description of the conversation flow:
{{ current_state_description }}
Follow this description, and exercise good judgment about when it is appropriate to deviate.{% endif %}

You will be provided the history of your conversation with the user up until now and the current state of the artifact.
Note that if the value for a field in the artifact is 'Unanswered', it means that the field has not been completed.
You need to select the best possible action(s), given the state of the conversation and the artifact.

Your job is to create a list of field updates to update the artifact. Each update should be listed as:

update_artifact_field(required parameters: field, value)

- You should pick this action as soon as (a) the user provides new information that is not already reflected in the current state of the artifact and (b) you are able to submit a valid value for a field in the artifact using this new information. If you have already updated a field in the artifact and there is no new information to update the field with, you should not pick this action.
- Make sure the value adheres to the constraints of the field as specified in the artifact schema.
- If the user has provided all required information to complete a field (i.e. the criteria for "Send message to user" are not satisfied) but the information is in the wrong format, you should not ask the user to reformat their response. Instead, you should simply update the field with the correctly formatted value. For example, if the artifact asks for the date of birth in the format "YYYY-MM-DD", and the user provides their date of birth as "June 15, 2000", you should update the field with the value "2000-06-15".
- Prioritize accuracy over completion. You should never make up information or make assumptions in order to complete a field. For example, if the field asks for a 10-digit phone number, and the user provided a 9-digit phone number, you should not add a digit to the phone number in order to complete the field. Instead, you should follow-up with the user to ask for the correct phone number. If they still aren't able to provide one, you should leave the field unanswered.
- If the user isn't able to provide all of the information needed to complete a field, use your best judgment to determine if a partial answer is appropriate (assuming it adheres to the formatting requirements of the field). For example, if the field asks for a description of symptoms along with details about when the symptoms started, but the user isn't sure when their symptoms started, it's better to record the information they do have rather than to leave the field unanswered (and to indicate that the user was unsure about the start date).
- If it's possible to update multiple fields at once (assuming you're adhering to the above rules in all cases), you should do so. For example, if the user provides their full name and date of birth in the same message, you should select the "update artifact fields" action twice, once for each field.

Your task is to state your step-by-step reasoning for the best possible action(s), followed by a final recommendation of which update(s) to make, including all required parameters. Someone else will be responsible for executing the update(s) you select and they will only have access to your output (not any of the conversation history, artifact schema, or other context) so it is EXTREMELY important that you clearly specify the value of all required parameters for each update you make.
"""


class ArtifactUpdate(BaseModel):
    field: str
    value: Any


class ArtifactUpdates(BaseModel):
    updates: list[ArtifactUpdate]


async def generate_artifact_updates(
    language_model: LanguageModel,
    definition: GCDefinition,
    artifact: Artifact,
    conversation: Conversation,
    max_retries: int = 2,
) -> list[ArtifactUpdate]:
    # Use the language model to generate artifact updates.

    completion_args = {
        "model": "gpt-4o",
        "messages": [
            create_system_message(
                UPDATE_ARTIFACT_TEMPLATE,
                {
                    "artifact_schema": artifact.get_schema_for_prompt(),
                    "context": definition.conversation_context,
                    "rules": definition.rules,
                    "current_state_description": definition.conversation_flow,
                },
            ),
        ],
        "response_format": ArtifactUpdates,
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
        artifact_updates = cast(ArtifactUpdates, completion.choices[0].message.parsed)

    # Check if each update is valid. If not, try to fix it a few times.

    good_updates: list[ArtifactUpdate] = []
    for update in artifact_updates.updates:
        attempts: list[UpdateAttempt] = []
        while len(attempts) < max_retries:
            # Don't try again if the attribute doesn't exist. Just skip this update.
            if not hasattr(artifact, update.field):
                logger.warning(
                    f"Field {update.field} is not a valid field for this artifact.", extra=add_serializable_data(update)
                )
                continue

            # If the update value isn't the right type, though, try to fix it.
            if not isinstance(getattr(artifact, update.field), type(update.value)):
                attempts.append(
                    UpdateAttempt(
                        field_value=update.value,
                        error=f"Value is not the right type. Got {type(update.value)} but expected {type(getattr(artifact, update.field))}.",
                    )
                )
                try:
                    new_field_value = await generate_artifact_field_update_error_fix(
                        language_model, artifact, update.field, update.value, conversation, attempts
                    )
                except Exception:
                    # Do something here if it errored out.
                    pass
                else:
                    update = ArtifactUpdate(field=update.field, value=new_field_value)

            # If it's the right type, we're good to go.
            else:
                good_updates.append(update)
                break

        # Failed.
        logger.warning(f"Updating field {update.field} has failed too many times. Skipping.")

    return good_updates
