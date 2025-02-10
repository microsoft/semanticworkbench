from typing import Optional

from assistant_drive import Drive
from openai_client.chat_driver import ChatDriverConfig
from skill_library import ActionCallable, ChatDriverFunctions, RunContext, RunContextProvider, Skill, SkillDefinition
from skill_library.routine import RoutineTypes
from skill_library.types import LanguageModel

from common_skill.actions import answer_question_about_content, bing_search, get_content_from_url, summarize
from common_skill.routines.deep_web_research import get_deep_web_research_routine
from common_skill.routines.demo_program_routine import get_demo_program_routine

from .actions import generate_research_plan, gpt_complete, select_user_intent, web_search
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

        action_functions: list[ActionCallable] = [
            self.answer_question_about_content,
            self.bing_search,
            self.get_content_from_url,
            self.gpt_complete,
            self.make_research_plan,
            self.select_user_intent,
            self.summarize,
            self.update_research_plan,
            self.web_search,
        ]

        routines: list[RoutineTypes] = [
            get_demo_action_list_routine(self.skill_name),
            get_demo_program_routine(self.skill_name),
            get_deep_web_research_routine(self.skill_name),
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

    ##################################
    # Action functions
    ##################################

    async def answer_question_about_content(
        self, run_context: RunContext, content: str, question: str, max_length: Optional[int]
    ) -> str:
        """
        Generate an answer to a question from the provided content.
        """
        content, metadata = await answer_question_about_content(self.language_model, content, question, max_length)
        return content

    async def bing_search(
        self, run_context: RunContext, search_description: str, max_results: Optional[int]
    ) -> list[str]:
        """
        Bing search using the search_description. Returns max_results URLs.
        """
        urls = await bing_search(search_description, max_results)
        return urls

    async def get_content_from_url(self, run_context: RunContext, url: str, max_length: Optional[int]) -> str:
        """
        Get the content from a URL.
        """
        content, metadata = await get_content_from_url(url, max_length)
        return content

    async def gpt_complete(self, run_context: RunContext, prompt: str) -> str:
        """
        Use the vast knowledge of GPT-4 completion using any prompt you provide.
        All information needed for the prompt should be in the prompt. No other
        context or content is available from anywhere other than this prompt.
        Don't refer to content outside the prompt. The prompt can be big.
        Returns the completion.
        """
        content, metadata = await gpt_complete(self.language_model, prompt)
        return content

    async def make_research_plan(self, run_context: RunContext, topic: str) -> list[str]:
        """
        Generate a research plan on a given topic. The plan will consist of a
        set of research questions to be answered.
        """
        content, metadata = await generate_research_plan(self.language_model, topic)
        return content

    async def select_user_intent(self, run_context: RunContext, options: dict[str, str]) -> str:
        """
        Select the user's intent from a set of options based on the conversation
        history.
        """
        content, metadata = await select_user_intent(run_context, self.language_model, options)
        return content

    async def summarize(
        self, run_context: RunContext, content: str, aspect: Optional[str], max_length: Optional[int]
    ) -> str:
        """
        Summarize the content from the given aspect. The content may be relevant or
        not to a given aspect. If no aspect is provided, summarize the content as
        is.
        """
        content, metadata = await summarize(self.language_model, content, aspect, max_length)
        return content

    async def update_research_plan(self, run_context: RunContext, topic: str) -> list[str]:
        """
        Update a research plan using information from the ongoing conversation.
        The plan will consist of an updated set of research questions to be
        answered.
        """
        content, metadata = await generate_research_plan(self.language_model, topic)
        return content

    async def web_search(self, run_context: RunContext, query: str) -> str:
        """
        Bing search using the search_description. Returns summarized web content
        from the top web search results to specifically answer the search
        description. Only necessary for facts and info not contained in GPT-4.
        """
        content, metadata = await web_search(self.language_model, query)
        return content


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
