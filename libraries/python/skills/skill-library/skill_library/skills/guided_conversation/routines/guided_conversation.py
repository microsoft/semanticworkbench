import importlib
import json
from typing import Any, cast

from events import InformationEvent, MessageEvent
from skill_library import AskUserFn, EmitFn, RunContext, RunRoutineFn
from skill_library.logging import extra_data, logger
from skill_library.skills.guided_conversation import ConversationGuide
from skill_library.skills.guided_conversation.agenda import Agenda
from skill_library.skills.guided_conversation.chat_completions.generate_agenda import generate_agenda
from skill_library.skills.guided_conversation.chat_completions.generate_artifact_updates import (
    generate_artifact_updates,
)
from skill_library.skills.guided_conversation.chat_completions.generate_final_artifact import final_artifact_update
from skill_library.skills.guided_conversation.chat_completions.generate_message import generate_message
from skill_library.skills.guided_conversation.guided_conversation_skill import (
    GuidedConversationSkill,
    NoDefinitionConfiguredError,
)
from skill_library.skills.guided_conversation.message import Conversation
from skill_library.skills.guided_conversation.resources import ConversationResource

DEFAULT_MAX_RETRIES = 3


async def main(
    context: RunContext,
    routine_state: dict[str, Any],
    emit: EmitFn,
    run: RunRoutineFn,
    ask_user: AskUserFn,
    conversation_guide: ConversationGuide | str | None = None,
    conversation: Conversation | None = None,
    resource: ConversationResource | None = None,
    agenda: Agenda | None = None,
    artifact: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Start a new guided conversation.

    This function is called when the conversation routine is started. It
    initializes the conversation state and starts the conversation.


    Vars for selecting the conversation guide:
        conversation_guide: You can supply a ConversationGuide or a string.
        If you use a string, a conversation guide by that name will be used
        from the `conversation_guides` module.

    Vars for prefilling state:
        resource: The current resource state.
        conversation: The current conversation state.
        agenda: The current agenda state.
        artifact: The current artifact state.

    Returns:
        tuple[bool, dict[str, Any] | None]: A tuple containing a boolean
        indicating if the conversation is complete and the current state of
        the artifact.
    """

    logger.debug(
        "Initializing guided conversation skill.",
        extra_data({"session_id": context.session_id, "vars": vars}),
    )

    skill = cast(GuidedConversationSkill, context.skills["common"])
    language_model = skill.language_model

    # The definition is required to run the conversation. It can be provided
    # in the skill config or as a param when initializing the conversation.
    guide = skill.guide
    if not guide:
        if not conversation_guide:
            raise NoDefinitionConfiguredError("No guide was provided to the skill.")

        match conversation_guide:
            case ConversationGuide():
                guide = conversation_guide
            case str():
                # Load the definition dynamically from the `conversation_guides` module.
                try:
                    guides_dir = "skill_library.skills.guided_conversation.conversation_guides"
                    guide_module_name = f"{guides_dir}.{conversation_guide}"
                    guide_module = importlib.import_module(guide_module_name)
                    guide = guide_module.definition
                except ImportError:
                    raise NoDefinitionConfiguredError(f"Could not import the definition module: {conversation_guide}")

    if conversation is None:
        conversation = Conversation()
    if resource is None:
        resource = ConversationResource(resource_constraint=guide.resource_constraint)
    if artifact is None:
        artifact = {}
    if agenda is None:
        agenda = Agenda()

    while True:
        logger.debug("Continuing guided conversation.", extra_data({"session_id": context.session_id}))

        # If it's not the first turn...
        if resource.turn_number > 0:
            # If it isn't the first turn, get the last message in the conversation.
            messages = (await context.conversation_history()).messages
            message = messages[-1].content
            conversation.add_user_message(message)

            # Update the artifact.
            try:
                artifact_updates = await generate_artifact_updates(
                    language_model, guide, artifact or {}, conversation, max_retries=DEFAULT_MAX_RETRIES
                )
            except Exception as e:
                # TODO: DO something with this error.
                logger.exception("Error generating artifact updates", exc_info=e)
            else:
                # Apply the validated updates to the artifact.
                for update in artifact_updates:
                    try:
                        artifact[update.field] = json.loads(update.value_as_json)
                    except json.JSONDecodeError:
                        logger.warning(f"Error decoding JSON for update: {update}")
                        continue
                emit(InformationEvent(message="Artifact updated", metadata={"artifact": artifact}))

        # Update agenda.
        try:
            agenda, is_done = await generate_agenda(
                language_model,
                guide,
                conversation,
                agenda,
                artifact,
                resource,
                max_retries=DEFAULT_MAX_RETRIES,
            )
            emit(InformationEvent(message="Agenda updated", metadata={"agenda": agenda.model_dump()}))
        except Exception:
            logger.exception("Error generating agenda")
            return artifact

        # If the agenda generation says we are done, generate the final
        # artifact.
        # TODO: Maybe we should put the check for "done" in the
        #   message generation function? Or... a separate function after the
        #   message is generated?
        if is_done:
            if artifact:
                artifact = await final_artifact_update(language_model, guide, conversation, artifact)
            emit(
                InformationEvent(
                    session_id=context.session_id, message="Conversation complete!", metadata={"artifact": artifact}
                )
            )
            return artifact

        # If we are not done, use the agenda to ask the user for whatever is next.
        else:
            message = await generate_message(language_model, guide, artifact, conversation)
            if message:
                conversation.add_assistant_message(message)
            emit(MessageEvent(session_id=context.session_id, message=message))

            # Increment the resource.
            resource.increment_resource()
