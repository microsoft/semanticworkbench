from openai_client.chat_driver import ChatDriverConfig
from skill_library import (
    ActionCallable,
    ChatDriverFunctions,
    InstructionRoutine,
    RoutineTypes,
    RunContext,
    RunContextProvider,
    Skill,
    SkillDefinition,
)

NAME = "your"
CLASS_NAME = "YourSkill"
DESCRIPTION = "Description of your skill."
DEFAULT_MAX_RETRIES = 3
INSTRUCTIONS = "You are an assistant that has access to the provided actions."


class YourSkill(Skill):
    def __init__(
        self,
        skill_definition: "YourSkillDefinition",
        run_context_provider: RunContextProvider,
    ) -> None:
        # Convenience variable to store the skill name.
        self.skill_name = skill_definition.name

        # Define some functions to be used as actions.
        action_functions: list[ActionCallable] = [
            self.example_action,
            self.example_with_parameters_action,
        ]

        # Add some routines.
        routines: list[RoutineTypes] = [
            self.example_routine(),
        ]

        # Configure the chat driver (if using). Register all the supplied actions to it as either
        # commands, functions, or both.
        if skill_definition.chat_driver_config:
            skill_definition.chat_driver_config.instructions = INSTRUCTIONS
            skill_definition.chat_driver_config.commands = ChatDriverFunctions(
                action_functions, run_context_provider
            ).all()
            skill_definition.chat_driver_config.functions = ChatDriverFunctions(
                action_functions, run_context_provider
            ).all()

        super().__init__(
            skill_definition=skill_definition,
            run_context_provider=run_context_provider,
            actions=action_functions,
            routines=routines,
        )

    ##################################
    # Routines
    ##################################

    def example_routine(self) -> InstructionRoutine:
        """
        Update this routine description.
        """
        return InstructionRoutine(
            name="template_example",  # name of routine
            skill_name=self.skill_name,
            description="Description of what the routine does.",
            routine=("template_example_action\ntemplate_example_with_parameters_action bar\n"),
        )

    ##################################
    # Actions
    ##################################

    def example_action(self, run_context: RunContext) -> None:
        """
        Update this action description.
        """
        pass

    def example_with_parameters_action(self, run_context: RunContext, foo: str) -> None:
        """
        Update this action description.
        """
        pass


class YourSkillDefinition(SkillDefinition):
    def __init__(
        self,
        name: str,
        description: str | None = None,
        chat_driver_config: ChatDriverConfig | None = None,
        # Any other parameters you want to pass to the skill.
    ) -> None:
        self.name = name
        self.description = description or DESCRIPTION
        self.chat_driver_config = chat_driver_config
        self.skill_class = YourSkill
