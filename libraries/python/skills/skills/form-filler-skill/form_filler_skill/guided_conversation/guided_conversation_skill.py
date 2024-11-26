import json
from typing import Any, Optional

from assistant_drive import Drive
from events import MessageEvent
from openai_client.chat_driver import ChatDriverConfig
from pydantic import BaseModel
from skill_library import RoutineTypes, Skill, StateMachineRoutine
from skill_library.run_context import RunContext
from skill_library.types import LanguageModel

from .agenda import Agenda
from .chat_drivers.final_artifact_update import final_artifact_update
from .chat_drivers.generate_artifact_updates import generate_artifact_updates
from .chat_drivers.generate_message import generate_message
from .chat_drivers.update_agenda import generate_agenda
from .definition import GCDefinition
from .logging import logger
from .message import Conversation
from .resources import GCResource, GCResourceData

CLASS_NAME = "GuidedConversationSkill"
DESCRIPTION = "Walks the user through a conversation about gathering info for the creation of an artifact."
DEFAULT_MAX_RETRIES = 3
INSTRUCTIONS = "You are an assistant."


class Artifact(BaseModel):
    pass

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"


class GuidedConversationSkill(Skill):
    def __init__(
        self,
        name: str,
        language_model: LanguageModel,
        drive: Drive,
        definition: GCDefinition | None = None,
        # agenda: Optional[Agenda] = None,
        # artifact: Optional[Artifact] = None,
        # resource: Optional[GCResource] = None,
        # conversation: Optional[Conversation] = None,
        chat_driver_config: ChatDriverConfig | None = None,
    ) -> None:
        self.language_model = language_model
        self.drive = drive

        # Configuring the definition of a conversation here makes this skill
        # instance for this one type of conversation. Alternatively, we could
        # also have the conversation_init_function take in the definition as a
        # parameter if we wanted to use the same instance for different kinds of
        # conversations.
        if definition:
            self.drive.write_model(
                definition,
                "GCDefinition.json",
            )
        else:
            definition = self.drive.read_model(GCDefinition, "GCDefinition.json")
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
        return StateMachineRoutine(
            name="conversation",
            description="Run a guided conversation.",
            init_function=self.conversation_init_function,
            step_function=self.conversation_step_function,
            skill=self,
        )

    async def conversation_init_function(self, context: RunContext, vars: dict[str, Any] | None = None):
        if vars is None:
            vars = {}

        # if vars is None or vars.get("artifact") is None:
        #     raise ValueError("The artifact must be provided to start the conversation.")

        # We can put all this data in the routine frame, or we could also put it
        # in the skill drive. All of this intermediate state can just go in the
        # frame. Only the final artifact needs to be saved to the drive.
        async with context.stack_frame_state() as state:
            state["resource"] = vars.get("resource") or GCResource(self.definition.resource_constraint).to_data()
            state["conversation"] = vars.get("conversation") or Conversation()
            state["agenda"] = vars.get("agenda") or Agenda()
            state["artifact"] = vars.get("artifact")

        # For guided conversation, we want to go ahead and run the first step.
        await self.conversation_step_function(context)

    async def conversation_step_function(
        self,
        context: RunContext,
        message: Optional[str] = None,
    ) -> tuple[bool, Artifact | None]:
        """
        The original GC code is a bit more complex than this, but this is a
        simplified version of the code.

        Original:

        ``` while not max_decision_retries:
            plan = kernel_function_generate_plan success, plugins,
            terminal_plugins = execute_plan(plan) if not
            success:
                max_decision_retries += 1 continue

            # run each tool: update_artifact, update_agenda, send_msg, end_conv
        ```

        Note that in this flow, the "plan" is like an action chooser and the
        plugins are like actions. We don't need any of that part because we
        actually just want to run an artifact update and an agenda update on
        every step.

        However, we do need to have the model generate which agenda items to
        update and which artifact items to update.

        The flow:
        - add user message to conversation
        - while not max_decision_retries:
            - run function/conversation_plan template to produce a conversation plan (aka reasoning):
                - Update agenda (required parameters: items)
                - Update artifact fields (required parameters: field, value)
                - Send message to user (required parameters: message)
                - End conversation (required parameters: None)

            - run function/execution template to produce the tool calls w/ args for all the things.
            - Parse result with gc.execute_plan method into sucess, plugins, terminal_plugins
            - try again if not a success

            - update artifact with tool calls (update the actual data object)
                - if error, try to fix with plugins/artifact/_fix_artifact_error (ARTIFACT_ERROR_CORRECTION_SYSTEM_TEMPLATE)
            - update agenda with tool calls (update the actual data object)
                - if error, try to fix with plugins/agenda/_fix_agenda_error (AGENDA_ERROR_CORRECTION_SYSTEM_TEMPLATE)
            - if user message: return user message with tool calls and increment resource (end turn)
            - if end conversation:
                - run functions/final_update_plan to produce a final conversation plan that only does update artifact tool calls
                - run function/execution template to with only agenda update tools calls to produce tool calls w/ args
                - run tool calls to update artifact, update all messages
                - increment resource and return final message (end turn, end convo)
        - increment resource and return error message (inc resource)

        Revised flow will be:
        if not first time:
            - updates = generate_artifact_updates
            - apply_updates(updates)
        - agenda, done = generate_new_agenda
        - if done:
            - artifact = generate_final_artifact
        - else:
            - generate_message
        """

        async with context.stack_frame_state() as state:
            definition = self.definition
            resource = GCResource.from_data(GCResourceData(**state["resource"]))
            conversation = Conversation(**state["conversation"])
            agenda = Agenda(**state["agenda"])

            if message:
                conversation.add_user_message(message)
                state["conversation"] = conversation

            # Update artifact, if we have one (we won't on first run).
            artifact: Artifact | None
            if state.get("artifact") is not None:
                artifact = Artifact(**state["artifact"])
                try:
                    # This function should generate VALID updates.
                    artifact_updates = await generate_artifact_updates(
                        self.language_model, definition, artifact, conversation, max_retries=DEFAULT_MAX_RETRIES
                    )
                except Exception as e:
                    # DO something with this error.
                    logger.fatal(f"Error generating artifact updates: {e}")
                else:
                    # Apply the updates to the artifact.
                    for update in artifact_updates:
                        value = json.loads(update.value_as_json)
                        artifact.__setattr__(update.field, value)
                    state["artifact"] = artifact
            else:
                artifact = None

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
                if artifact is None:
                    state["artifact"] = Artifact()
                context.emit(MessageEvent(message="Agenda updated"))
            except Exception:
                # TODO: DO something with this error.
                return False, artifact
            else:
                # If the agenda generation says we are done, generate the final artifact.
                if is_done:
                    if artifact:
                        artifact = await final_artifact_update(self.language_model, definition, conversation, artifact)
                    context.emit(MessageEvent(session_id=context.session_id, message="Conversation complete!"))
                    return True, artifact

                # If we are not done, use the agenda to ask the user for whatever is next.
                else:
                    message = await generate_message(
                        self.language_model, definition, artifact, conversation, max_retries=DEFAULT_MAX_RETRIES
                    )
                    context.emit(MessageEvent(session_id=context.session_id, message=message))
                    return False, artifact

    ##################################
    # Actions
    ##################################

    # None, yet.
