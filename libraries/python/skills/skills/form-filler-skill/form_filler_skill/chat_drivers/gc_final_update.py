import logging

from chat_driver import ChatDriver, ChatDriverConfig, ContextProtocol
from chat_driver.in_memory_message_history_provider import InMemoryMessageHistoryProvider
from chat_driver.message_formatter import liquid_format
from form_filler_skill.guided_conversation.artifact import Artifact
from form_filler_skill.guided_conversation.conversation_helpers import Conversation
from form_filler_skill.guided_conversation.definition import GCDefinition
from openai import AsyncAzureOpenAI, AsyncOpenAI

logger = logging.getLogger(__name__)


final_update_template = """<message role="system">You are a helpful, thoughtful, and meticulous assistant.
You just finished a conversation with a user.{% if context %} Here is some additional context about the conversation:
{{ context }}{% endif %}

Your goal is to complete an artifact as thoroughly and accurately as possible based on the conversation.

This is the schema of the artifact:
{{ artifact_schema }}

You will be given the current state of the artifact as well as the conversation history.
Note that if the value for a field in the artifact is 'Unanswered', it means that the field was not completed. \
Some fields may have already been completed during the conversation.

Your need to determine whether there are any fields that need to be updated, and if so, update them.
- You should only update a field if both of the following conditions are met: (a) the current state does NOT adequately reflect the conversation \
and (b) you are able to submit a valid value for a field. \
You are allowed to update completed fields, but you should only do so if the current state is inadequate, \
e.g. the user corrected a mistake in their date of birth, but the artifact does not show the corrected version. \
Remember that it's always an option to reset a field to "Unanswered" - this is often the best choice if the artifact contains incorrect information that cannot be corrected. \
Do not submit a value that is identical to the current state of the field (e.g. if the field is already "Unanswered" and the user didn't provide any new information about it, you should not submit "Unanswered"). \
- Make sure the value adheres to the constraints of the field as specified in the artifact schema. \
If it's not possible to update a field with a valid value (e.g., the user provided an invalid date of birth), you should not update the field.
- If the artifact schema is open-ended (e.g. it asks you to rate how pressing the user's issue is, without specifying rules for doing so), \
use your best judgment to determine whether you have enough information to complete the field based on the conversation.
- Prioritize accuracy over completion. You should never make up information or make assumptions in order to complete a field. \
For example, if the field asks for a 10-digit phone number, and the user provided a 9-digit phone number, you should not add a digit to the phone number in order to complete the field.
- If the user wasn't able to provide all of the information needed to complete a field, \
use your best judgment to determine if a partial answer is appropriate (assuming it adheres to the formatting requirements of the field). \
For example, if the field asks for a description of symptoms along with details about when the symptoms started, but the user wasn't sure when their symptoms started, \
it's better to record the information they do have rather than to leave the field unanswered (and to indicate that the user was unsure about the start date).
- It's possible to update multiple fields at once (assuming you're adhering to the above rules in all cases). It's also possible that no fields need to be updated.

Your task is to state your step-by-step reasoning about what to update, followed by a final recommendation.
Someone else will be responsible for executing the updates and they will only have access to your output \
(not any of the conversation history, artifact schema, or other context) so make sure to specify exactly which \
fields to update and the values to update them with, or to state that no fields need to be updated.
</message>

<message role="user">Conversation history:
{{ conversation_history }}

Current state of the artifact:
{{ artifact_state }}</message>"""


async def final_update(
    context: ContextProtocol,
    open_ai_client: AsyncOpenAI | AsyncAzureOpenAI,
    definition: GCDefinition,
    chat_history: Conversation,
    artifact: Artifact,
):
    history = InMemoryMessageHistoryProvider(formatter=liquid_format)

    history.append_system_message(
        final_update_template,
        {
            "conversation_history": chat_history.get_repr_for_prompt(),
            "context": definition.conversation_context,
            "artifact_schema": artifact.get_schema_for_prompt(),
            "artifact_state": artifact.get_artifact_for_prompt(),
        },
    )

    config = ChatDriverConfig(
        context=context,
        openai_client=open_ai_client,
        model="gpt-3.5-turbo",
        message_provider=history,
    )

    chat_driver = ChatDriver(config)
    return await chat_driver.respond()