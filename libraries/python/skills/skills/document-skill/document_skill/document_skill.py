# flake8: noqa
# ruff: noqa

from openai_client.chat_driver import ChatDriverConfig
from openai import AsyncAzureOpenAI, AsyncOpenAI
from pydantic import BaseModel  # temp to have something to experiment with
from skill_library import EmitterType, RoutineTypes, Skill
from skill_library.routine import InstructionRoutine, ProgramRoutine

from .chat_drivers import draft_content, draft_outline
from .chat_drivers.get_user_feedback_for_outline_decision import get_user_feedback_for_outline_decision

NAME = "document_skill"
DESCRIPTION = "Anything related to documents - creation, edit, translation"


class Attachment(BaseModel):
    filename: str
    content: str


class Outline(BaseModel):
    version: int = 0
    content: str


class Content(BaseModel):
    content: str  # Content/fragment/page that is created will likely have
    # data associated with it... not sure what more at this point.


class Paper(BaseModel):
    version: int = 0
    contents: list[Content] = []


class DocumentSkillContext:
    def __init__(self) -> None:
        # TODO: Pull in all this state from a Drive.
        self.chat_history: str = ""
        self.attachments_list: list[Attachment] = []
        self.outline_versions: list[Outline] = []
        self.paper_versions: list[Paper] = []


class DocumentSkill(Skill):
    def __init__(
        self, emit: EmitterType, chat_driver_config: ChatDriverConfig, openaai_client: AsyncAzureOpenAI | AsyncOpenAI
    ) -> None:
        self.openai_client = openaai_client
        self.document_skill_context: DocumentSkillContext = DocumentSkillContext()

        actions = [
            # self.ask_user,
            self.draft_content,
            self.draft_outline,
            self.get_user_feedback_decision,
        ]

        routines: list[RoutineTypes] = [
            self.test_instruction_routine(),
        ]

        # Configure the skill's chat driver.
        chat_driver_config.commands = actions
        chat_driver_config.functions = actions

        super().__init__(
            name=NAME,
            description=DESCRIPTION,
            chat_driver_config=chat_driver_config,
            actions=actions,
            routines=routines,
        )

    ##################################
    # Routines
    ##################################

    def test_instruction_routine(self) -> InstructionRoutine:
        """
        Update this routine description.
        """
        return InstructionRoutine(
            name="test_instruction_routine",
            description="Description of what the routine does.",
            routine=("test_action"),
            skill=self,
        )

    def template_example_routine(self) -> ProgramRoutine:
        """
        Update this routine description.
        """
        return ProgramRoutine(
            name="template_example_routine",
            description="Description of what the routine does.",
            program=("TBD"),
            skill=self,
        )

    ##################################
    # Actions
    ##################################
    async def draft_content(
        self,
        session_id: str,
        decision: str | None = None,
        user_feedback: str | None = None,
    ) -> str:
        response = await draft_content(
            session_id=session_id,
            open_ai_client=self.openai_client,
            chat_history=self.document_skill_context.chat_history,
            attachments=self.document_skill_context.attachments_list,
            outline_versions=self.document_skill_context.outline_versions,
            paper_versions=self.document_skill_context.paper_versions,
            user_feedback=user_feedback,
            decision=decision,
        )
        return response.message or ""

    async def draft_outline(
        self, session_id: str, decision: str | None = None, user_feedback: str | None = None
    ) -> str:
        response = await draft_outline(
            session_id=session_id,
            open_ai_client=self.openai_client,
            chat_history=self.document_skill_context.chat_history,
            attachments=self.document_skill_context.attachments_list,
            outline_versions=self.document_skill_context.outline_versions,
            user_feedback=user_feedback,
        )
        return response.message or ""

    async def get_user_feedback_decision(self, session_id: str, user_feedback: str, outline: bool) -> str:
        response = await get_user_feedback_for_outline_decision(
            session_id=session_id,
            open_ai_client=self.openai_client,
            chat_history=self.document_skill_context.chat_history,
            outline_versions=self.document_skill_context.outline_versions,
            paper_versions=self.document_skill_context.paper_versions,
            user_feedback=user_feedback,
            outline=outline,
        )
        return response.message or ""

    async def routine(self, session_id: str):
        # Define these vars here to make the following routine look more like a PROGRAM routine.
        document_skill = self

        async def ask_user(question: str) -> str:
            return "hello world"

        # Routine.
        decision = "[ITERATE]"
        user_feedback: str | None = None
        while decision == "[ITERATE]":
            await document_skill.draft_outline(session_id, user_feedback=user_feedback)
            user_feedback = await ask_user("This look good?")
            decision = await document_skill.get_user_feedback_decision(session_id, user_feedback, outline=True)
        if decision == "[QUIT]":
            exit()
        await document_skill.draft_content(session_id)
        user_feedback = await ask_user("This look good?")
        decision = await document_skill.get_user_feedback_decision(session_id, user_feedback, outline=False)
        content = ""
        while decision != "[QUIT]":
            content = await document_skill.draft_content(session_id, user_feedback=user_feedback, decision=decision)
            decision, user_feedback = await document_skill.get_user_feedback_decision(
                session_id, user_feedback, outline=False
            )
        return content

        # decision = "[ITERATE]"
        # while decision == "[ITERATE]":
        #     document_skill.draft_outline(user_feedback=user_feedback, history=assistant.chat_history)
        #      guided_conversation.run()
        #     user_feedback = await ask_user("This look good?")
        #     decision = document_skill.get_user_feedback_decision(user_feedback, outline=True)
        # if decision == "[QUIT]":
        #     exit()
        # document_skill.draft_content()
        # user_feedback = ask_user("This look good?")
        # decision = document_skill.get_user_feedback_decision(user_feedback, outline=False)
        # while decision != "[QUIT]":
        #     content = document_skill.draft_content(user_feedback=user_feedback, decision=decision)
        #     decision, user_feedback = await document_skill.get_user_feedback_decision(
        #         context, user_feedback, outline=False
        #     )
        # return content
