from typing import Any, Optional

from openai_client.chat_driver import ChatDriverConfig
from skill_library import RoutineTypes, Skill, StateMachineRoutine
from skill_library.run_context import RunContext
from skill_library.types import LanguageModel

CLASS_NAME = "FormFillerSkill"
DESCRIPTION = "Walks the user through uploading and filling out a form."
DEFAULT_MAX_RETRIES = 3
INSTRUCTIONS = "You are an assistant."


class FormFillerSkill(Skill):
    def __init__(
        self,
        name: str,
        chat_driver_config: ChatDriverConfig,
        language_model: LanguageModel,
    ) -> None:
        # Put all functions in a group. We are going to use all these as (1)
        # skill actions, but also as (2) chat functions and (3) chat commands.
        # You can also put them in separate lists if you want to differentiate
        # between these.
        functions = []

        # Add some skill routines.
        routines: list[RoutineTypes] = [
            self.form_filler_routine(),
        ]

        # Re-configure the skill's chat driver.
        chat_driver_config.instructions = INSTRUCTIONS
        chat_driver_config.commands = functions
        chat_driver_config.functions = functions

        # TODO: change where this is from.
        self.openai_client = chat_driver_config.openai_client

        # Initialize the skill!
        super().__init__(
            name=name,
            description=DESCRIPTION,
            chat_driver_config=chat_driver_config,
            actions=functions,
            routines=routines,
        )

    ##################################
    # Routines
    ##################################

    def form_filler_routine(self) -> StateMachineRoutine:
        return StateMachineRoutine(
            name="form_filler",
            description="Run a form-filler routine.",
            init_function=self.form_fill_init,
            step_function=self.form_fill_step,
            skill=self,
        )

    async def form_fill_init(self, context: RunContext, vars: dict[str, Any] | None = None):
        # TODO: Use `vars` to config the form filler routine.
        await self.form_fill_step(context)

    async def form_fill_step(
        self,
        context: RunContext,
        message: Optional[str] = None,
    ) -> str | None:
        FormFiller = self
        state = await context.get_state()
        while True:
            match state.get("mode"):
                case None:
                    state["mode"] = "init"
                case "init":
                    # Cede control to guided conversation if an artifact needs to be generated.
                    # How do we want to pass in all the GC definitions? Should they just be a simpler config object TYPE?
                    if not state["artifact"]:
                        if not state["gce_id"]:
                            guided_conversation_vars: dict[str, Any] = {
                                "definition_type": "upload_files",
                                "objective": "Upload a form to be filled out by the form filler recipe.",
                            }
                            gc_id = await context.run_routine(
                                context, "guided_conversation.doc_upload", guided_conversation_vars
                            )
                            state["gc_id"] = gc_id
                        # TODO: What is the best way to subroutine?
                        # artifact = GuidedConversation.run(state["gce_id"], message)
                        # if artifact:
                        #     state["artifact"] = artifact
                        # else:
                        #     await context.set_state(state)
                        #     return

                    agenda, is_done = FormFiller.update_agenda(context)
                    state["agenda"] = agenda
                    if is_done:
                        state["mode"] = "done"
                    state["mode"] = "conversation"
                    await context.set_state(state)
                    return agenda
                case "conversation":
                    state["form"] = FormFiller.update_form(context)
                    agenda, is_done = FormFiller.update_agenda(context)
                    state["agenda"] = agenda
                    if is_done:
                        state["mode"] = "finalize"
                    await context.set_state(state)
                    return agenda
                case "finalize":
                    message = FormFiller.generate_filled_form(context)
                    state["mode"] = "done"
                    await context.set_state(state)
                    return message
                case "done":
                    return None

    ##################################
    # Actions
    ##################################

    def update_agenda(self, context: RunContext):
        return "message", False

    def update_form(self, context: RunContext):
        return "message", False

    def generate_filled_form(self, context: RunContext):
        return "message"
