from pathlib import Path
from typing import Any

import pytest
from assistant_drive import Drive, DriveConfig
from form_filler_skill.guided_conversation.definitions.acrostic_poem import definition
from form_filler_skill.guided_conversation.guided_conversation_skill import GuidedConversationSkill
from openai_client import AzureOpenAIAzureIdentityAuthConfig, AzureOpenAIServiceConfig, create_client
from openai_client.config import first_env_var
from pydantic import HttpUrl
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

    # Configure the skill and its dependencies.
    drive = Drive(DriveConfig(root=Path(__file__).parent / ".data"))
    skill = GuidedConversationSkill(
        name="guided_conversation", language_model=language_model, definition=definition, drive=drive
    )
    skill_dependency_tree: dict[str, Skill] = {"guided_conversation": skill}

    # Create a routine run function.
    async def run_routine(name: str, vars: dict[str, Any] | None = None) -> Any:
        await skill_registry.run_routine_by_designation(runContext, name, vars)

    # Set up a run context.
    path = Path(__file__).parent / ".data"
    drive = Drive(DriveConfig(root=path))
    routine_stack = RoutineStack(drive)
    skill_registry = SkillRegistry(skill_dependency_tree, routine_stack)
    runContext = RunContext("test-session-1", drive, LogEmitter().emit, routine_stack, run_routine)

    # Run the skill with it's context.
    await skill.conversation_init_function(context=runContext)

    finished = False
    artifact = None
    while not finished:
        user_message = input("You: ")
        finished, artifact = await skill.conversation_step_function(runContext, user_message)

    assert artifact is not None
    print(artifact)
