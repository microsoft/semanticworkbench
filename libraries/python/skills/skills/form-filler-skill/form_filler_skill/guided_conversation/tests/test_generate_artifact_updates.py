import os

import pytest
from form_filler_skill.guided_conversation.agenda import Agenda
from form_filler_skill.guided_conversation.chat_drivers.generate_artifact_updates import generate_artifact_updates
from form_filler_skill.guided_conversation.chat_drivers.update_agenda import generate_agenda
from form_filler_skill.guided_conversation.definitions import acrostic_poem
from form_filler_skill.guided_conversation.definitions.acrostic_poem import Artifact, definition
from form_filler_skill.guided_conversation.message import Conversation
from form_filler_skill.guided_conversation.resources import GCResource
from openai_client import AzureOpenAIAzureIdentityAuthConfig, AzureOpenAIServiceConfig, create_client
from pydantic import HttpUrl
from skill_library.types import LanguageModel


@pytest.fixture
def client() -> LanguageModel:
    azure_openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
    if not azure_openai_endpoint or not azure_openai_deployment:
        # FIXME: Paul, make sure this is in your environment.
        azure_openai_endpoint = "https://lightspeed-team-shared-openai-eastus.openai.azure.com/"
        azure_openai_deployment = "gpt-4o"
        # pytest.skip("AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_DEPLOYMENT must be available in the environment.")

    service_config = AzureOpenAIServiceConfig(
        auth_config=AzureOpenAIAzureIdentityAuthConfig(),
        azure_openai_endpoint=HttpUrl(azure_openai_endpoint),
        azure_openai_deployment=azure_openai_deployment,
    )
    return create_client(service_config)


@pytest.mark.skip("For manual testing.")
async def test_generate_artifact_updates(client: LanguageModel) -> None:
    artifact = Artifact()
    conversation = Conversation().add_user_message("Hi!")

    response = await generate_artifact_updates(client, definition, artifact, conversation)
    expected_response = "hi"
    assert response == expected_response


@pytest.mark.skip("For manual testing.")
async def test_generage_agenda(client: LanguageModel) -> None:
    conversation = Conversation().add_user_message("Hi!")
    agenda = Agenda()
    artifact = None
    definition = acrostic_poem.definition
    resource = GCResource(definition.resource_constraint)
    agenda, is_done = await generate_agenda(
        client,
        definition,
        conversation,
        agenda,
        artifact,
        resource,
    )
    assert agenda is not None
    assert not is_done
