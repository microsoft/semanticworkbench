from assistant_drive import Drive
from openai_client.chat_driver import ChatDriverConfig
from skill_library import ActionCallable, ChatDriverFunctions, RunContext, RunContextProvider, Skill, SkillDefinition
from skill_library.routine import RoutineTypes
from skill_library.types import LanguageModel

from common_skill.routines.demo_program_routine import get_demo_program_routine

from .actions import gpt_complete, web_search
from .routines.demo_action_list_routine import get_demo_action_list_routine

CLASS_NAME = "CommonSkill"
DESCRIPTION = "Provides common actions and routines."
INSTRUCTIONS = "You are an assistant."


class CommonSkill(Skill):
    def __init__(
        self,
        skill_definition: "CommonSkillDefinition",
        run_context_provider: RunContextProvider,
    ) -> None:
        self.skill_name = skill_definition.name
        self.language_model = skill_definition.language_model
        self.drive = skill_definition.drive

        action_functions: list[ActionCallable] = ActionFunctions(
            skill_definition.language_model
        ).list_action_functions()

        routines: list[RoutineTypes] = [
            get_demo_action_list_routine(self.skill_name),
            get_demo_program_routine(self.skill_name),
        ]

        # Configure the skill's chat driver. This is just used for testing the
        # skill out directly, but won't be exposed in the assistant.
        if skill_definition.chat_driver_config:
            chat_driver_commands = ChatDriverFunctions(action_functions, run_context_provider).all()
            chat_driver_functions = ChatDriverFunctions(action_functions, run_context_provider).all()
            skill_definition.chat_driver_config.commands = chat_driver_commands
            skill_definition.chat_driver_config.functions = chat_driver_functions

        # Initialize the skill!
        super().__init__(
            skill_definition=skill_definition,
            run_context_provider=run_context_provider,
            actions=action_functions,
            routines=routines,
        )


class ActionFunctions:
    """
    Using a class like this might be a good pattern for declaring actions. It
    allows the injection of things while allowing the method signature from
    /list_actions to not need to include them. FOr example, the `gpt_complete`
    method needs a language model, but we can just initialize it to use the
    skill's language model (above).
    """

    def __init__(self, language_model: LanguageModel) -> None:
        self.language_model = language_model

    async def gpt_complete(self, run_context: RunContext, prompt: str) -> str:
        content, metadata = await gpt_complete(self.language_model, prompt)
        return content

    async def web_search(self, run_context: RunContext, query: str) -> str:
        content, metadata = await web_search(self.language_model, query)
        return content

    def list_action_functions(self) -> list[ActionCallable]:
        return [self.gpt_complete, self.web_search]


class CommonSkillDefinition(SkillDefinition):
    def __init__(
        self,
        name: str,
        language_model: LanguageModel,
        drive: Drive,
        description: str | None = None,
        chat_driver_config: ChatDriverConfig | None = None,
    ) -> None:
        self.language_model = language_model
        self.drive = drive

        if chat_driver_config:
            chat_driver_config.instructions = INSTRUCTIONS

        # Initialize the skill!
        super().__init__(
            name=name,
            skill_class=CommonSkill,
            description=description or DESCRIPTION,
            chat_driver_config=chat_driver_config,
        )
