from typing import Callable, Type

from assistant_drive import Drive
from openai_client.chat_driver import ChatDriverConfig
from skill_library import RunContext, RunContextProvider, Skill, SkillDefinition
from skill_library.routine import RoutineTypes
from skill_library.types import LanguageModel

from .actions import gpt_complete, web_search

CLASS_NAME = "CommonSkill"
DESCRIPTION = "Provides common actions and routines."
INSTRUCTIONS = "You are an assistant."


class CommonSkill(Skill):
    def __init__(
        self,
        skill_definition: "CommonSkillDefinition",
        run_context_provider: RunContextProvider,
    ) -> None:
        self.language_model = skill_definition.language_model
        self.drive = skill_definition.drive

        routines: list[RoutineTypes] = []
        actions: list[Callable] = Actions(skill_definition.language_model).list_actions()

        # Configure the skill's chat driver. This is just used for testing the
        # skill out directly, but won't be exposed in the assistant.
        if skill_definition.chat_driver_config:
            skill_definition.chat_driver_config.instructions = INSTRUCTIONS

        # Initialize the skill!
        super().__init__(
            skill_definition=skill_definition,
            run_context_provider=run_context_provider,
            actions=actions,
            routines=routines,
        )


"""
1. RunContext gets passed in during execution.
2. Other variables can be passed in during initialization.
3. When a person runs /list_actions, they shouldn't see RunContext or the initialization variables.
4. A person should be able to run an action with params excluding RunContext and inits.
5. The chatdriver should be able to have registered actions without runcontext or init variables. The function that is given to the chatdriver should not have these things.
  A. A chat driver should be able to specify it wants to run a tool call, but the function that executes it should inject a run context?? Or not... the functions themselves might be defined within a context that has a run context.

"""


class Actions:
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

    def list_actions(self) -> list[Callable]:
        return [self.gpt_complete, self.web_search]


class CommonSkillDefinition(SkillDefinition):
    def __init__(
        self,
        name: str,
        language_model: LanguageModel,
        drive: Drive,
        chat_driver_config: ChatDriverConfig | None = None,
        skill_class: Type[Skill] = CommonSkill,
    ) -> None:
        self.language_model = language_model
        self.drive = drive

        if chat_driver_config:
            chat_driver_config.instructions = INSTRUCTIONS

        # Initialize the skill!
        super().__init__(
            name=name,
            skill_class=skill_class,
            description=DESCRIPTION,
            chat_driver_config=chat_driver_config,
        )
