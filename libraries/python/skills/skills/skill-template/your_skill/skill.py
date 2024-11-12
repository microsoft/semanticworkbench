from chat_driver import ChatDriverConfig
from context import ContextProtocol
from skill_library import InstructionRoutine, RoutineTypes, Skill

NAME = "your"
CLASS_NAME = "YourSkill"
DESCRIPTION = "Description of your skill."
DEFAULT_MAX_RETRIES = 3
INSTRUCTIONS = "You are an assistant that has access to the provided actions."


class YourSkill(Skill):
    def __init__(
        self,
        chat_driver_config: ChatDriverConfig,
    ) -> None:
        # Add some actions.
        actions = [
            self.example_action,
            self.example_with_parameters_action,
        ]

        # Add some routines.
        routines: list[RoutineTypes] = [
            self.example_routine(),
        ]

        # Configure the chat driver (if using). Register all the supplied actions to it as either
        # commands, functions, or both.
        chat_driver_config.instructions = INSTRUCTIONS
        chat_driver_config.commands = actions
        chat_driver_config.functions = actions

        super().__init__(
            name=NAME,
            description=DESCRIPTION,
            chat_driver_config=chat_driver_config,
            skill_actions=actions,
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
            "template_example",  # name of routine
            "Description of what the routine does.",
            routine=("template_example_action\ntemplate_example_with_parameters_action bar\n"),
            skill=self,
        )

    ##################################
    # Actions
    ##################################

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
