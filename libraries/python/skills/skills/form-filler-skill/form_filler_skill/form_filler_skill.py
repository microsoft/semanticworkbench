from typing import Any, Optional

from openai_client.chat_driver import ChatDriverConfig
from skill_library import (
    ChatDriverFunctions,
    RoutineTypes,
    RunContext,
    RunContextProvider,
    Skill,
    SkillDefinition,
    StateMachineRoutine,
)
from skill_library.types import LanguageModel

CLASS_NAME = "FormFillerSkill"
DESCRIPTION = "Walks the user through uploading and filling out a form."
DEFAULT_MAX_RETRIES = 3
INSTRUCTIONS = "You are an assistant."


class FormFillerSkill(Skill):
    def __init__(
        self,
        skill_definition: "FormFillerSkillDefinition",
        run_context_provider: RunContextProvider,
    ) -> None:
        self.skill_name = skill_definition.name

        action_functions = []

        # Add some skill routines.
        routines: list[RoutineTypes] = [
            self.form_filler_routine(),
        ]

        # Re-configure the skill's chat driver.
        if skill_definition.chat_driver_config:
            chat_driver_commands = ChatDriverFunctions(action_functions, run_context_provider).all()
            chat_driver_functions = ChatDriverFunctions(action_functions, run_context_provider).all()
            skill_definition.chat_driver_config.instructions = INSTRUCTIONS
            skill_definition.chat_driver_config.commands = chat_driver_commands
            skill_definition.chat_driver_config.functions = chat_driver_functions

        self.openai_client = skill_definition.language_model

        # Initialize the skill!
        super().__init__(
            skill_definition=skill_definition,
            run_context_provider=run_context_provider,
            actions=action_functions,
            routines=routines,
        )

    ##################################
    # Routines
    ##################################

    def form_filler_routine(self) -> StateMachineRoutine:
        return StateMachineRoutine(
            name="form_filler",
            skill_name=self.skill_name,
            description="Run a form-filler routine.",
            init_function=self.form_fill_init,
            step_function=self.form_fill_step,
        )

    async def form_fill_init(self, context: RunContext, vars: dict[str, Any] | None = None):
        # TODO: Use `vars` to config the form filler routine.
        return await self.form_fill_step(context)

    async def form_fill_step(
        self,
        run_context: RunContext,
        message: Optional[str] = None,
    ) -> tuple[bool, str | None]:
        FormFiller = self
        state = await run_context.get_state()
        while True:
            match state.get("mode"):
                case None:
                    state["mode"] = "init"
                case "init":
                    # Cede control to guided conversation if an artifact needs to be generated.
                    # How do we want to pass in all the GC definitions? Should they just be a simpler config object TYPE?
                    if not state["artifact"]:
                        if not state["gce_id"]:
                            pass
                            # guided_conversation_vars: dict[str, Any] = {
                            #     "definition_type": "upload_files",
                            #     "objective": "Upload a form to be filled out by the form filler recipe.",
                            # }
                            # gc_id = await run_context.run_routine(
                            #     "guided_conversation.doc_upload", **guided_conversation_vars
                            # )
                            # state["gc_id"] = gc_id
                        # TODO: What is the best way to subroutine?
                        # artifact = GuidedConversation.run(state["gce_id"], message)
                        # if artifact:
                        #     state["artifact"] = artifact
                        # else:
                        #     await context.set_state(state)
                        #     return

                    agenda, is_done = FormFiller.update_agenda(run_context)
                    state["agenda"] = agenda
                    if is_done:
                        state["mode"] = "done"
                    state["mode"] = "conversation"
                    await run_context.set_state(state)
                    return is_done, agenda
                case "conversation":
                    state["form"] = FormFiller.update_form(run_context)
                    agenda, is_done = FormFiller.update_agenda(run_context)
                    state["agenda"] = agenda
                    if is_done:
                        state["mode"] = "finalize"
                    await run_context.set_state(state)
                    return is_done, agenda
                case "finalize":
                    message = FormFiller.generate_filled_form(run_context)
                    state["mode"] = "done"
                    await run_context.set_state(state)
                    return False, message
                case "done":
                    return True, None

    ##################################
    # Actions
    ##################################

    def update_agenda(self, context: RunContext):
        message = "message"
        is_done = False
        return message, is_done

    def update_form(self, context: RunContext):
        return "message", False

    def generate_filled_form(self, context: RunContext):
        return "message"


class FormFillerSkillDefinition(SkillDefinition):
    def __init__(
        self,
        name: str,
        language_model: LanguageModel,
        description: str | None = None,
        chat_driver_config: ChatDriverConfig | None = None,
    ) -> None:
        self.name = name
        self.language_model = language_model
        self.description = description or DESCRIPTION
        self.chat_driver_config = chat_driver_config
        self.skill_class = FormFillerSkill
