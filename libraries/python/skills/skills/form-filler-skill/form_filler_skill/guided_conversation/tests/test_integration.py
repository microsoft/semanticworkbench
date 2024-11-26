from pathlib import Path
from textwrap import dedent

import pytest
from assistant_drive import Drive, DriveConfig
from form_filler_skill.guided_conversation.definition import GCDefinition
from form_filler_skill.guided_conversation.guided_conversation_skill import GuidedConversationSkill
from form_filler_skill.guided_conversation.resources import (
    ResourceConstraint,
    ResourceConstraintMode,
    ResourceConstraintUnit,
)
from openai_client import AzureOpenAIAzureIdentityAuthConfig, AzureOpenAIServiceConfig, create_client
from openai_client.config import first_env_var
from pydantic import BaseModel, Field, HttpUrl
from skill_library import Skill
from skill_library.routine_stack import RoutineStack
from skill_library.run_context import LogEmitter, RunContext
from skill_library.skill_registry import SkillRegistry


@pytest.mark.skip("For manual testing.")
async def test_poem_feedback():
    service_config = AzureOpenAIServiceConfig(
        auth_config=AzureOpenAIAzureIdentityAuthConfig(),
        azure_openai_endpoint=HttpUrl(first_env_var("azure_openai_endpoint", "assistant__azure_openai_endpoint") or ""),
        azure_openai_deployment=first_env_var("azure_openai_deployment", "assistant__azure_openai_deployment")
        or "gpt-3.5-turbo",
    )
    language_model = create_client(service_config)

    class Artifact(BaseModel):
        student_poem: str = Field(description="The acrostic poem written by the student.")
        initial_feedback: str = Field(description="Feedback on the student's final revised poem.")
        final_feedback: str = Field(description="Feedback on how the student was able to improve their poem.")
        inappropriate_behavior: list[str] = Field(
            description=dedent("""
                List any inappropriate behavior the student attempted while chatting with you.
                It is ok to leave this field Unanswered if there was none.
                """)
        )

    definition = GCDefinition(
        artifact_schema=Artifact.model_json_schema(),
        rules=[
            "DO NOT write the poem for the student.",
            "Terminate the conversation immediately if the students asks for harmful or inappropriate content.",
        ],
        conversation_flow=dedent("""
            1. Start by explaining interactively what an acrostic poem is.
            2. Then give the following instructions for how to go ahead and write one:
                1. Choose a word or phrase that will be the subject of your acrostic poem.
                2. Write the letters of your chosen word or phrase vertically down the page.
                3. Think of a word or phrase that starts with each letter of your chosen word or phrase.
                4. Write these words or phrases next to the corresponding letters to create your acrostic poem.
            3. Then give the following example of a poem where the word or phrase is HAPPY:
                Having fun with friends all day,
                Awesome games that we all play.
                Pizza parties on the weekend,
                Puppies we bend down to tend,
                Yelling yay when we win the game
            4. Finally have the student write their own acrostic poem using the word or phrase of their choice. Encourage them
            to be creative and have fun with it. After they write it, you should review it and give them feedback on what they
            did well and what they could improve on. Have them revise their poem based on your feedback and then review it again.
        """),
        conversation_context=dedent("""
            You are working 1 on 1 a 4th grade student who is chatting with you in the computer lab at school while being
            supervised by their teacher.
        """),
        resource_constraint=ResourceConstraint(
            quantity=10,
            unit=ResourceConstraintUnit.TURNS,
            mode=ResourceConstraintMode.EXACT,
        ),
    )

    # Configure the skill and its dependencies.
    drive = Drive(DriveConfig(root=Path(__file__).parent / ".data"))
    skill = GuidedConversationSkill(
        name="guided_conversation", language_model=language_model, definition=definition, drive=drive
    )
    skill_dependency_tree: dict[str, Skill] = {"guided_conversation": skill}

    # Set up a run context.
    path = Path(__file__).parent / ".data"
    drive = Drive(DriveConfig(root=path))
    routine_stack = RoutineStack(drive)
    skill_registry = SkillRegistry(skill_dependency_tree, routine_stack)
    runContext = RunContext(
        "test-session-1", drive, LogEmitter().emit, routine_stack, skill_registry.run_routine_by_designation
    )

    # Run the skill with it's context.
    await skill.conversation_init_function(context=runContext)

    finished = False
    artifact = None
    while not finished:
        user_message = input("You: ")
        finished, artifact = await skill.conversation_step_function(runContext, user_message)

    assert artifact is not None
    print(artifact)
