import pytest
from guided_conversation_skill.chat_drivers.generate_artifact_updates import generate_artifact_updates
from guided_conversation_skill.definitions.acrostic_poem import definition
from guided_conversation_skill.message import Conversation
from skill_library.types import LanguageModel


@pytest.mark.skip("For manual testing.")
async def test_generate_artifact_updates(client: LanguageModel) -> None:
    artifact = {}
    conversation = Conversation().add_user_message("Hi!")
    response = await generate_artifact_updates(client, definition, artifact, conversation)
    expected_response = []
    assert response == expected_response
