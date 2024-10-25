from typing import Any, Optional

from chat_driver import ChatDriverConfig
from context import Context
from skill_library import FunctionRoutine, RoutineTypes, Skill
from skill_library.skill_registry import SkillRegistry

from form_filler_skill.guided_conversation.definition import GCDefinition

from .chat_drivers.gc_final_update import final_update
from .chat_drivers.gc_update_agenda import update_agenda
from .chat_drivers.gc_update_artifact import update_artifact

NAME = "guided-conversation"
CLASS_NAME = "GuidedConversationSkill"
DESCRIPTION = (
    "Walks the user through a conversation about gathering info for the creation of an artifact."
)
DEFAULT_MAX_RETRIES = 3
INSTRUCTIONS = "You are an assistant."


class GuidedConversationSkill(Skill):
    def __init__(
        self,
        chat_driver_config: ChatDriverConfig,
    ) -> None:
        # Put all functions in a group. We are going to use all these as (1)
        # skill actions, but also as (2) chat functions and (3) chat commands.
        # You can also put them in separate lists if you want to differentiate
        # between these.
        functions = [
            self.update_agenda,
            self.update_artifact,
            self.final_update,
        ]

        # Add some skill routines.
        routines: list[RoutineTypes] = [
            self.conversation_routine,
        ]

        # Configure the skill's chat driver.
        chat_driver_config.instructions = INSTRUCTIONS
        chat_driver_config.commands = functions
        chat_driver_config.functions = functions

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

    async def conversation_init_function(
        self, skill_registry: SkillRegistry, context: Context, vars: Optional[dict[str, Any]]
    ):
        if vars is None:
            return
        state = {"definition": vars["definition"]}
        skill_registry.routine_stack.update_current_state(state)
        await self.conversation_step_function(skill_registry, context)

    async def conversation_step_function(
        self,
        skill_registry: SkillRegistry,
        context: Context,
        message: Optional[str] = None,
    ):
        frame = skill_registry.routine_stack.peek()
        state = frame.state if frame else {}
        definition = GCDefinition(**state["definition"])
        while True:
            match state["mode"]:
                case None:
                    state["mode"] = "init"
                case "init":
                    state["chat_history"] = []
                    message, done = self.update_agenda(context, definition)
                    if done:
                        state["mode"] = "finalize"
                    state["mode"] = "conversation"
                    runner.send(message)
                    return
                case "conversation":
                    state["chat_history"] += message
                    state["artifact"] = self.update_artifact(context)
                    message, done = self.update_agenda()
                    if done:
                        state["mode"] = "finalize"
                    runner.send(message)
                    return
                case "finalize":
                    message = self.final_update()
                    state["state"] = "done"
                    runner.send(message)
                    return
                case "done":
                    return state["artifact"]

    ##################################
    # Actions
    ##################################

    def update_agenda(self, context: Context, definition: GCDefinition):
        update_agenda(
            context,
            self.openai_client,
            definition,
            self.chat_driver.message_provider.get(),
        )

    def update_artifact(self, context: Context):
        update_artifact(context)

    def final_update(self, context: Context):
        final_update(context)
