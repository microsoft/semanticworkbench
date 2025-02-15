import json
from typing import Any

from openai_client import (
    CompletionError,
    create_system_message,
    create_user_message,
    make_completion_args_serializable,
    validate_completion,
)
from skill_library.skills.guided_conversation.artifact_helpers import get_artifact_for_prompt, get_schema_for_prompt
from skill_library.types import LanguageModel

from ..guide import ConversationGuide
from ..logging import add_serializable_data, logger
from ..message import Conversation

FINAL_UPDATE_TEMPLATE = """
You are a helpful, thoughtful, and meticulous assistant.

You just finished a conversation with a user.

{% if context %}
Here is some additional context about the conversation:
{{ context }}
{% endif %}

Your goal is to complete an artifact as thoroughly and accurately as possible based on the conversation.

This is the schema of the artifact:
{{ artifact_schema }}

You will be given the current state of the artifact as well as the conversation history. Note that if a required field from the artifact schema is missing from the artifact, it means that the field was not completed.

You need to determine whether there are any fields that need to be updated, and if so, update them.

- You should only update a field if both of the following conditions are met: (a) the current state does NOT adequately reflect the conversation and (b) you are able to submit a valid value for a field. You are allowed to update completed fields, but you should only do so if the current state is inadequate, e.g. the user corrected a mistake in their date of birth, but the artifact does not show the corrected version. Remember that it's always an option to delete a field - this is often the best choice if the artifact contains incorrect information that cannot be corrected. Do not submit a value that is identical to the current state of the field.
- Make sure the value adheres to the constraints of the field as specified in the artifact schema. If it's not possible to update a field with a valid value (e.g., the user provided an invalid date of birth), you should not update the field.
- If the artifact schema is open-ended (e.g. it asks you to rate how pressing the user's issue is, without specifying rules for doing so), use your best judgment to determine whether you have enough information to complete the field based on the conversation.
- Prioritize accuracy over completion. You should never make up information or make assumptions in order to complete a field. For example, if the field asks for a 10-digit phone number, and the user provided a 9-digit phone number, you should not add a digit to the phone number in order to complete the field.
- If the user wasn't able to provide all of the information needed to complete a field, use your best judgment to determine if a partial answer is appropriate (assuming it adheres to the formatting requirements of the field). For example, if the field asks for a description of symptoms along with details about when the symptoms started, but the user wasn't sure when their symptoms started, it's better to record the information they do have rather than to leave the field unanswered (and to indicate that the user was unsure about the start date).
- It's possible to update multiple fields at once (assuming you're adhering to the above rules in all cases). It's also possible that no fields need to be updated.

Your task is to return the final artifact as json.
""".replace("\n\n\n", "\n\n").strip()

USER_MESSAGE_TEMPLATE = """Conversation history:
{{ conversation_history }}

Current state of the artifact:
{{ artifact_state }}"""


async def final_artifact_update(
    language_model: LanguageModel,
    definition: ConversationGuide,
    conversation: Conversation,
    artifact: dict[str, Any],
) -> dict[str, Any]:
    completion_args = {
        "model": "gpt-4o",
        "messages": [
            create_system_message(
                FINAL_UPDATE_TEMPLATE,
                {
                    "context": definition.conversation_context,
                    "artifact_schema": get_schema_for_prompt(definition.artifact_schema),
                },
            ),
            create_user_message(
                USER_MESSAGE_TEMPLATE,
                {
                    "conversation_history": str(conversation),
                    "artifact_state": get_artifact_for_prompt(artifact),
                },
            ),
        ],
        "response_format": {"type": "json_object"},
    }

    metadata = {}
    logger.debug("Completion call.", extra=add_serializable_data(make_completion_args_serializable(completion_args)))
    metadata["completion_args"] = make_completion_args_serializable(completion_args)
    try:
        completion = await language_model.chat.completions.create(
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
        return artifact
    else:
        raw_json = completion.choices[0].message.content or ""
        return json.loads(raw_json)
