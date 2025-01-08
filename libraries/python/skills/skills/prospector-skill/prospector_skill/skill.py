from context import ContextProtocol
from openai_client.chat_driver import ChatDriverConfig
from skill_library import (
    ChatDriverFunctions,
    InstructionRoutine,
    RoutineTypes,
    RunContextProvider,
    Skill,
    SkillDefinition,
)

NAME = "prospector"
CLASS_NAME = "ProspectorSkill"
DESCRIPTION = "A skill that assists you in mining information from your files to help you complete tasks."
DEFAULT_MAX_RETRIES = 3
INSTRUCTIONS = "You are an assistant that has access to the provided actions."


class ProspectorSkill(Skill):
    def __init__(
        self,
        skill_definition: "ProspectorSkillDefinition",
        run_context_provider: RunContextProvider,
    ) -> None:
        self.skill_name = skill_definition.name

        # Add some actions.
        action_functions = [
            self.gather_information_action,
            self.create_draft_action,
            self.example_action,
            self.example_with_parameters_action,
        ]

        # Add some routines.
        routines: list[RoutineTypes] = [
            self.draft_grant_proposal_routine(),
            self.example_routine(),
        ]

        # Configure the chat driver (if using). Register all the supplied actions to it as either
        # commands, functions, or both.
        if skill_definition.chat_driver_config:
            chat_driver_commands = ChatDriverFunctions(action_functions, run_context_provider).all()
            chat_driver_functions = ChatDriverFunctions(action_functions, run_context_provider).all()
            skill_definition.chat_driver_config.commands = chat_driver_commands
            skill_definition.chat_driver_config.functions = chat_driver_functions

        super().__init__(
            skill_definition=skill_definition,
            run_context_provider=run_context_provider,
            actions=action_functions,
            routines=routines,
        )

    ##################################
    # Routines
    ##################################

    def draft_grant_proposal_routine(self) -> InstructionRoutine:
        """
        Update this routine description.
        """
        return InstructionRoutine(
            name="draft_grant_proposal",
            skill_name=self.skill_name,
            description="Draft a grant proposal.",
            routine=("gather_information_action\ncreate_draft_action\n"),
        )

    def example_routine(self) -> InstructionRoutine:
        """
        Update this routine description.
        """
        return InstructionRoutine(
            name="template_example",
            skill_name=self.skill_name,
            description="Description of what the routine does.",
            routine=("template_example_action\ntemplate_example_with_parameters_action bar\n"),
        )

    ##################################
    # Actions
    ##################################

    def gather_information_action(self, context: ContextProtocol) -> None:
        """
        Update this action description.
        """
        pass

    def create_draft_action(self, context: ContextProtocol) -> None:
        """
        Update this action description.
        """
        pass

    def example_action(self, context: ContextProtocol) -> None:
        """
        Update this action description.
        """
        pass

    def example_with_parameters_action(self, context: ContextProtocol, foo: str) -> None:
        """
        Update this action description.
        """
        pass


class ProspectorSkillDefinition(SkillDefinition):
    def __init__(
        self,
        name: str,
        description: str | None = None,
        chat_driver_config: ChatDriverConfig | None = None,
        skill_class: type[Skill] = Skill,
    ) -> None:
        if chat_driver_config:
            chat_driver_config.instructions = INSTRUCTIONS

        # Initialize the skill!
        super().__init__(
            name=name,
            skill_class=skill_class,
            description=description or DESCRIPTION,
            chat_driver_config=chat_driver_config,
        )
