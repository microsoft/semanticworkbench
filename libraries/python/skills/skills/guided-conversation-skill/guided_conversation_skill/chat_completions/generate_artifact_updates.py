import json
from typing import Annotated, Any, cast

import jsonschema
from guided_conversation_skill.artifact_helpers import (
    InvalidArtifactFieldError,
    UpdateAttempt,
    get_artifact_for_prompt,
    get_field_schema_string,
    get_schema_for_prompt,
    validate_field_presence_in_schema,
    validate_field_value,
)
from guided_conversation_skill.definition import ConversationGuide
from openai_client import (
    CompletionError,
    add_serializable_data,
    create_system_message,
    create_user_message,
    make_completion_args_serializable,
    validate_completion,
)
from pydantic import BaseModel, Field
from skill_library.types import LanguageModel

from ..logging import logger
from ..message import Conversation, ConversationMessageType
from .fix_artifact_error import generate_artifact_field_update_error_fix

UPDATE_ARTIFACT_TEMPLATE = """
You are a helpful, thoughtful, and meticulous assistant. You are conducting a conversation with a user. Your goal is to complete an artifact as thoroughly as possible by the end of the conversation, and to ensure a smooth experience for the user.

This is the schema of the artifact you are completing:
{{ artifact_schema }}

{% if context %}
Here is some additional context about the conversation:
{{ context }}
{% endif %}

Throughout the conversation, you must abide by these rules:
{{ rules }}

{% if current_state_description %}
Here's a description of the conversation flow:
{{ current_state_description }}

Follow this description, and exercise good judgment about when it is appropriate to deviate.
{% endif %}

You will be provided the history of your conversation with the user up until now and the current state of the artifact. Note that if a required field from the artifact schema is not present in the artifact, it means that the field has not been completed. You need to select the best update(s), given the state of the conversation and the artifact.

Your job is to create a list of field updates to update the artifact using only the information provided by the user. Each update should be listed as a dictionary with two keys: 'field' and 'value_as_json'. The 'field' key should contain the name of the field in the artifact that you want to update, and the 'value_as_json' key should contain the new value for that field in JSON format. Only use fields that are present in the artifact schema.

- Create field updates only if (a) the user provides new information that is not already reflected in the current state of the artifact and (b) you are able to submit a valid value for a field in the artifact using this new information. If you have already updated a field in the artifact and there is no new information to update the field with, you should not create a field update.
- Make sure the value adheres to the constraints of the field as specified in the artifact schema.
- If the user has provided all required information to complete a field but the information is in the wrong format, you should not ask the user to reformat their response. Instead, you should simply update the field with the correctly formatted value. For example, if the artifact asks for the date of birth in the format "YYYY-MM-DD", and the user provides their date of birth as "June 15, 2000", you should update the field with the value "2000-06-15".
- Prioritize accuracy over completion. You should never make up information or make assumptions in order to complete a field. For example, if the field asks for a 10-digit phone number, and the user provided a 9-digit phone number, you should not add a digit to the phone number in order to complete the field. Instead, you should follow-up with the user to ask for the correct phone number. If they still aren't able to provide one, don't update the artifact field.
- If the user isn't able to provide all of the information needed to complete a field, use your best judgment to determine if a partial answer is appropriate (assuming it adheres to the formatting requirements of the field). For example, if the field asks for a description of symptoms along with details about when the symptoms started, but the user isn't sure when their symptoms started, it's better to record the information they do have rather than to leave the field unanswered (and to indicate that the user was unsure about the start date).
- If it's possible to update multiple fields at once (assuming you're adhering to the above rules in all cases), you should do so. For example, if the user provides their full name and date of birth in the same message, you should select the "update artifact fields" action twice, once for each field.
- If the user's message contains no information relevant to updating the artifact, you should not create any field updates. For example, if the user sends a message that says "Hello" or "Goodbye", you should not create any field updates.

Your task is to state your step-by-step reasoning for the best possible action(s), followed by a final recommendation of which update(s) to make, including all required parameters. Someone else will be responsible for executing the update(s) you select and they will only have access to your output (not any of the conversation history, artifact schema, or other context) so it is EXTREMELY important that you clearly specify the value of all required parameters for each update you make.
""".replace("\n\n\n", "\n\n")


class ArtifactUpdate(BaseModel):
    field: Annotated[str, Field(description="The name of a field from the artifact schema.")]
    value_as_json: Annotated[str, Field(description="The value to update the field with as a JSON string.")]


class ArtifactUpdates(BaseModel):
    """A list of updates to be applied to an artifact."""

    step_by_step_reasoning: str
    updates: list[ArtifactUpdate]


async def generate_artifact_updates(
    language_model: LanguageModel,
    definition: ConversationGuide,
    artifact: dict[str, Any],
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
                    "artifact_schema": get_schema_for_prompt(definition.artifact_schema),
                    "context": definition.conversation_context,
                    "rules": definition.rules,
                    # "current_state_description": definition.conversation_flow,
                },
            ),
            create_user_message(
                ("Conversation history:\n{{ chat_history }}\n\nCurrent state of the artifact:\n{{ artifact }}"),
                {
                    "chat_history": str(conversation.exclude([ConversationMessageType.REASONING])),
                    "artifact_state": get_artifact_for_prompt(artifact),
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
    except Exception as e:
        completion_error = CompletionError(e)
        metadata["completion_error"] = completion_error.message
        logger.error(
            completion_error.message,
            extra=add_serializable_data({"completion_error": completion_error.body, "metadata": metadata}),
        )
        raise completion_error from e
    else:
        artifact_updates = cast(ArtifactUpdates, completion.choices[0].message.parsed)

    # Check if each update is valid. If not, try to fix it a few times.
    good_updates: list[ArtifactUpdate] = []
    for update in artifact_updates.updates:
        failed_attempts: list[UpdateAttempt] = []
        try:
            attempt_failure = validate_update_attempt(definition.artifact_schema, update)
        except InvalidArtifactFieldError:
            # Don't try again if the attribute/field doesn't exist. Just skip
            # this update.
            continue

        while len(failed_attempts) < max_retries:
            if attempt_failure:
                failed_attempts.append(attempt_failure)
                try:
                    new_field_value = await generate_artifact_field_update_error_fix(
                        language_model,
                        definition.artifact_schema,
                        update.field,
                        update.value_as_json,
                        conversation,
                        failed_attempts,
                    )
                except Exception:
                    # Do something here if the fix attempt(s) were unsuccessful.
                    pass
                else:
                    update = ArtifactUpdate(field=update.field, value_as_json=new_field_value)
                    # Loop to check this new value out again.
                    continue

            # If it's the right type, we're good to go.
            else:
                good_updates.append(update)
                break

        if len(failed_attempts) >= max_retries:
            logger.warning(f"Updating field {update.field} has failed too many times. Skipping.")

    return good_updates


def validate_update_attempt(artifact_schema: dict[str, Any], update: "ArtifactUpdate") -> UpdateAttempt | None:
    """
    Validate an update attempt against an artifact schema.
    """

    # Throw an error if it's not in the schema.
    validate_field_presence_in_schema(artifact_schema, update.field)

    type_string = get_field_schema_string(artifact_schema, update.field)
    attempt_failure: "UpdateAttempt | None" = None

    try:
        update_value = json.loads(update.value_as_json)
    except Exception:
        update_value = update.value_as_json

    try:
        validate_field_value(artifact_schema, update.field, update_value)
    except jsonschema.ValidationError:
        attempt_failure = UpdateAttempt(
            field_value=update_value,
            error=f"Parsed value is not the right type. Got `{type(update_value)}` but expected `{type_string}`.",
        )

    return attempt_failure
