import importlib
import json
from typing import Any, Optional

from assistant_drive import Drive
from events import InformationEvent, MessageEvent
from openai_client.chat_driver import ChatDriverConfig
from skill_library import Skill
from skill_library.routine import RoutineTypes, StateMachineRoutine
from skill_library.run_context import RunContext
from skill_library.types import LanguageModel

from .agenda import Agenda
from .chat_completions.final_artifact_update import final_artifact_update
from .chat_completions.generate_artifact_updates import generate_artifact_updates
from .chat_completions.generate_message import generate_message
from .chat_completions.update_agenda import generate_agenda
from .guide import ConversationGuide
from .logging import add_serializable_data, logger
from .message import Conversation
from .resources import GCResource

CLASS_NAME = "GuidedConversationSkill"
DESCRIPTION = "Walks the user through a conversation about gathering info for the creation of an artifact."
DEFAULT_MAX_RETRIES = 3
INSTRUCTIONS = "You are an assistant."


class NoDefinitionConfiguredError(Exception):
    pass


class GuidedConversationSkill(Skill):
    def __init__(
        self,
        name: str,
        language_model: LanguageModel,
        drive: Drive,
        definition: ConversationGuide | None = None,
        # agenda: Optional[Agenda] = None,
        # artifact: Optional[Artifact] = None,
        # resource: Optional[GCResource] = None,
        # conversation: Optional[Conversation] = None,
        chat_driver_config: ChatDriverConfig | None = None,
    ) -> None:
        self.language_model = language_model
        self.drive = drive

        # Configuring the definition of a conversation here makes this skill
        # instance for this one type (definition) of conversation.
        # Alternatively, you can not supply a definition and have the
        # conversation_init_function take in the definition as a parameter if
        # you wanted to use the same instance for different kinds of
        # conversations.
        if definition:
            # If a definition is supplied, we'll use this for every
            # conversation. Save it so we can use it when this skill is run
            # again in the future.
            self.drive.write_model(
                definition,
                "GCDefinition.json",
            )
        else:
            # As a convenience, check to see if a definition was already saved
            # previously in this drive.
            try:
                definition = self.drive.read_model(ConversationGuide, "GCDefinition.json")
            except FileNotFoundError:
                logger.warning(
                    "No definition supplied or found in the drive. Will expect one as a var in the conversation_init_function"
                )

        self.definition = definition

        # Initialize resources.
        # if artifact is None:
        #     artifact = Artifact(**self.definition.artifact_schema)
        # if resource is None:
        #     resource = GCResource(self.definition.resource_constraint)
        # if conversation is None:
        #     conversation = Conversation()

        # These normally won't be passed in (they are created within the skill),
        # but this is helpful for testing.
        # self.agenda = self._config(Agenda, agenda)
        # self.artifact = self._config(Artifact, artifact)
        # self.resource = self._config(GCResource, resource)
        # self.conversation = self._config(Conversation, conversation)

        # Add the skill routines.
        routines: list[RoutineTypes] = [
            self.conversation_routine(),
        ]

        # Configure the skill's chat driver. This is just used for testing the
        # skill out directly, but won't be exposed in the assistant.
        if chat_driver_config:
            chat_driver_config.instructions = INSTRUCTIONS

        # Initialize the skill!
        super().__init__(
            name=name,
            description=DESCRIPTION,
            chat_driver_config=chat_driver_config,
            actions=[],
            routines=routines,
        )

    ##################################
    # Routines
    ##################################

    def conversation_routine(self) -> StateMachineRoutine:
        """
        Conduct a guided conversation with the user. This conversation will
        result in an artifact. The conversation will follow a defined flow and
        will update the artifact as the conversation progresses. If a resource
        constraint is reached, the conversation will end. An agenda will be
        created and followed to guide the conversation. Either supply a
        conversation definition in vars["definition"] or use a pre-configured
        definition by supplying the name of your definition in
        vars["conversation_type"]. Current conversation types you can use are:
        "acrostic_poem", "patient_intake", "er_triage", or "interview".
        """
        return StateMachineRoutine(
            name="conversation",
            description="Run a guided conversation.",
            init_function=self.conversation_init_function,
            step_function=self.conversation_step_function,
            skill=self,
        )

    async def conversation_init_function(
        self, context: RunContext, vars: dict[str, Any] | None = None
    ) -> tuple[bool, dict[str, Any] | None]:
        """
        Start a new guided conversation.

        This function is called when the conversation routine is started. It
        initializes the conversation state and starts the conversation.

        Args:
            context (RunContext): The context for the current run. vars
            (dict[str, Any], optional): Optional variables to pass in. Defaults
            to None.

        Vars:
            definition (optional): The definition of the conversation if not already supplied in the skill config.
            conversation_type (optional): Run a pre-defined conversation definition (in the `definitions` module).
            resource: The resource constraints for the conversation.
            conversation: The conversation state.
            agenda: The agenda state.
            artifact: The artifact state.

        Returns:
            tuple[bool, dict[str, Any] | None]: A tuple containing a boolean
            indicating if the conversation is complete and the current state of
            the artifact.
        """

        logger.debug(
            "Initializing guided conversation skill.",
            add_serializable_data({"session_id": context.session_id, "vars": vars}),
        )

        if vars is None:
            vars = {}

        # The definition is required to run the conversation. It can be provided
        # in the skill config or as a var when initializing the conversation.
        definition = self.definition
        if not definition:
            if "definition" in vars:
                definition = ConversationGuide(**vars["definition"])
            else:
                if "conversation_type" in vars:
                    # Load the definition dynamically from the `definitions`
                    # module.
                    try:
                        definitions_dir = "guided_conversation_skill.definitions"
                        definition_module_name = f"{definitions_dir}.{vars['conversation_type']}"
                        definition_module = importlib.import_module(definition_module_name)
                        definition = definition_module.definition
                    except ImportError:
                        raise NoDefinitionConfiguredError(
                            f"Could not import the definition module: {vars['conversation_type']}"
                        )
                else:
                    raise NoDefinitionConfiguredError("No definition was provided to the skill.")

        # We can put all this data in the routine frame, or we could also put it
        # in the skill drive. All of this intermediate state can just go in the
        # frame. Only the final artifact needs to be saved to the drive.
        async with context.stack_frame_state() as state:
            state["definition"] = definition
            state["conversation"] = vars.get("conversation") or Conversation()
            state["agenda"] = vars.get("agenda") or Agenda()
            state["artifact"] = vars.get("artifact", {})
            state["resource"] = GCResource(resource_constraint=definition.resource_constraint)

        # For guided conversation, we want to go ahead and run the first step.
        return await self.conversation_step_function(context)

    async def conversation_step_function(
        self,
        context: RunContext,
        message: Optional[str] = None,
    ) -> tuple[bool, dict[str, Any] | None]:
        logger.debug("Continuing guided conversation.", add_serializable_data({"session_id": context.session_id}))
        async with context.stack_frame_state() as state:
            definition = ConversationGuide(**state["definition"])
            conversation = Conversation(**state["conversation"])
            agenda = Agenda(**state["agenda"])
            artifact: dict[str, Any] = state.get("artifact", {})
            resource = GCResource(**state["resource"])

            if message:
                conversation.add_user_message(message)
                state["conversation"] = conversation

            # Update artifact, if it's not the first turn.
            if resource.turn_number > 0:
                try:
                    artifact_updates = await generate_artifact_updates(
                        self.language_model, definition, artifact or {}, conversation, max_retries=DEFAULT_MAX_RETRIES
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
                    state["artifact"] = artifact
                    context.emit(InformationEvent(message="Artifact updated", metadata={"artifact": artifact}))

            # Update agenda.
            try:
                agenda, is_done = await generate_agenda(
                    self.language_model,
                    definition,
                    conversation,
                    agenda,
                    artifact,
                    resource,
                    max_retries=DEFAULT_MAX_RETRIES,
                )
                state["agenda"] = agenda
                context.emit(InformationEvent(message="Agenda updated", metadata={"agenda": agenda.model_dump()}))
            except Exception:
                # TODO: DO something with this error?
                logger.exception("Error generating agenda")
                return False, artifact

            # If the agenda generation says we are done, generate the final
            # artifact.
            # TODO: Maybe we should put the check for "done" in the
            #   message generation function? Or... a separate function after the
            #   message is generated?
            if is_done:
                if artifact:
                    artifact = await final_artifact_update(self.language_model, definition, conversation, artifact)
                context.emit(
                    InformationEvent(
                        session_id=context.session_id, message="Conversation complete!", metadata={"artifact": artifact}
                    )
                )
                return True, artifact

            # If we are not done, use the agenda to ask the user for whatever is next.
            else:
                message = await generate_message(
                    self.language_model, definition, artifact, conversation, max_retries=DEFAULT_MAX_RETRIES
                )
                context.emit(MessageEvent(session_id=context.session_id, message=message))
                if message:
                    conversation.add_assistant_message(message)
                    state["conversation"] = conversation

                # Increment the resource.
                resource.increment_resource()
                state["resource"] = resource

                return False, artifact

    ##################################
    # Actions
    ##################################

    # None, yet.
