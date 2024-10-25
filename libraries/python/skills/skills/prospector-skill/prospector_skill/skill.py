from chat_driver import ChatDriverConfig
from context import ContextProtocol
from skill_library import InstructionRoutine, RoutineTypes, Skill

NAME = "prospector"
CLASS_NAME = "ProspectorSkill"
DESCRIPTION = "A skill that assists you in mining information from your files to help you complete tasks."
DEFAULT_MAX_RETRIES = 3
INSTRUCTIONS = "You are an assistant that has access to the provided actions."


class ProspectorSkill(Skill):
    def __init__(
        self,
        context: ContextProtocol,
        chat_driver_config: ChatDriverConfig,
    ) -> None:
        # Add some actions.
        actions = [
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
        chat_driver_config.instructions = INSTRUCTIONS
        chat_driver_config.context = context
        chat_driver_config.commands = actions
        chat_driver_config.functions = actions

        super().__init__(
            name=NAME,
            description=DESCRIPTION,
            context=context,
            chat_driver_config=chat_driver_config,
            skill_actions=actions,
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
            "draft_grant_proposal",  # name of routine
            "Draft a grant proposal.",  # description of routine
            routine=("gather_information_action\ncreate_draft_action\n"),
            skill=self,
        )

    def example_routine(self) -> InstructionRoutine:
        """
        Update this routine description.
        """
        return InstructionRoutine(
            "template_example",  # name of routine
            "Description of what the routine does.",
            routine=("template_example_action\ntemplate_example_with_parameters_action bar\n"),
            skill=self,
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
