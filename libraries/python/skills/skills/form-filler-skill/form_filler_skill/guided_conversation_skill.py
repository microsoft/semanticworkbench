# flake8: noqa
# ruff: noqa

from typing import Any, Optional

from openai_client.chat_driver import ChatDriverConfig
from events import BaseEvent, MessageEvent
from skill_library import EmitterType, FunctionRoutine, RoutineTypes, Skill
from skill_library.run_context import RunContext

from form_filler_skill.agenda import Agenda
from form_filler_skill.artifact import Artifact
from form_filler_skill.definition import GCDefinition
from form_filler_skill.message import Conversation
from form_filler_skill.resources import GCResource

from .chat_drivers.final_update import final_update
from .chat_drivers.unneeded.execute_reasoning import execute_reasoning
from .chat_drivers.update_agenda import update_agenda

NAME = "guided-conversation"
CLASS_NAME = "GuidedConversationSkill"
DESCRIPTION = "Walks the user through a conversation about gathering info for the creation of an artifact."
DEFAULT_MAX_RETRIES = 3
INSTRUCTIONS = "You are an assistant."


class GuidedConversationSkill(Skill):
    def __init__(
        self,
        chat_driver_config: ChatDriverConfig,
        emit: EmitterType,
        agenda: Agenda,
        artifact: Artifact,
        resource: GCResource,
    ) -> None:
        # Put all functions in a group. We are going to use all these as (1)
        # skill actions, but also as (2) chat functions and (3) chat commands.
        # You can also put them in separate lists if you want to differentiate
        # between these.
        functions = [
            self.update_agenda,
            self.execute_reasoning,
            self.final_update,
        ]

        # Add some skill routines.
        routines: list[RoutineTypes] = [
            self.conversation_routine(),
        ]

        # Configure the skill's chat driver.
        # TODO: change where this is from.
        self.openai_client = chat_driver_config.openai_client
        chat_driver_config.instructions = INSTRUCTIONS
        chat_driver_config.commands = functions
        chat_driver_config.functions = functions

        # TODO: Persist these. They should be saved in the skills state by
        # session_id.
        self.agenda = agenda
        self.artifact = artifact
        self.resource = resource
        self.chat_history = Conversation()

        self.emit = emit

        # Initialize the skill!
        super().__init__(
            name=NAME,
            description=DESCRIPTION,
            chat_driver_config=chat_driver_config,
            skill_actions=functions,
            routines=routines,
        )

    ##################################
    # Routines
    ##################################

    def conversation_routine(self) -> FunctionRoutine:
        return FunctionRoutine(
            name="conversation",
            description="Run a guided conversation.",
            init_function=self.conversation_init_function,
            step_function=self.conversation_step_function,
            skill=self,
        )

    async def conversation_init_function(self, context: RunContext, vars: dict[str, Any] | None = None):
        if vars is None:
            return
        state = {"definition": vars["definition"]}
        await context.routine_stack.set_current_state(state)
        await self.conversation_step_function(context)

    async def conversation_step_function(
        self,
        context: RunContext,
        message: Optional[str] = None,
    ):
        # TODO: Where is this conversation maintained?
        # FIXME: None of this works. WIP.
        frame = await context.routine_stack.peek()
        state = frame.state if frame else {}
        definition = GCDefinition(**state["definition"])
        while True:
            match state["mode"]:
                case None:
                    state["mode"] = "init"
                case "init":
                    state["chat_history"] = []
                    agenda, done = await self.update_agenda("")
                    if done:
                        state["mode"] = "finalize"
                    state["mode"] = "conversation"
                    self.emit(MessageEvent(message="Agenda updated"))
                    return
                case "conversation":
                    state["chat_history"] += message
                    # state["artifact"] = self.update_artifact(context)
                    agenda, done = await self.update_agenda("")
                    if agenda:
                        state["agenda"] = agenda
                    if done:
                        state["mode"] = "finalize"
                    # await self.message_user(context, agenda)  # generates the next message
                    return
                case "finalize":
                    # self.final_update()  # Generates the final message.
                    state["state"] = "done"
                    # runner.send(message)
                    return
                case "done":
                    return state["artifact"]

    ##################################
    # Actions
    ##################################

    async def update_agenda(self, items: str) -> tuple[Agenda, bool]:
        return await update_agenda(
            self.openai_client,
            items,
            self.chat_history,
            self.agenda,
            self.resource,
        )

    async def execute_reasoning(self, context: RunContext, reasoning: str) -> BaseEvent:
        return await execute_reasoning(self.openai_client, reasoning, self.artifact.get_schema_for_prompt())

    async def final_update(self, context: RunContext, definition: GCDefinition):
        await final_update(self.openai_client, definition, self.chat_history, self.artifact)
