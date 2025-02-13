import pytest
from skill_library.skills.guided_conversation.agenda import Agenda
from skill_library.skills.guided_conversation.chat_completions.generate_agenda import generate_agenda, resource_phrase
from skill_library.skills.guided_conversation.conversation_guides import acrostic_poem
from skill_library.skills.guided_conversation.message import Conversation
from skill_library.skills.guided_conversation.resources import ConversationResource, ResourceConstraintUnit
from skill_library.types import LanguageModel


@pytest.mark.skip("For manual testing.")
async def test_generate_agenda(client: LanguageModel) -> None:
    conversation = Conversation().add_user_message("Hi!")
    agenda = Agenda()
    artifact = {}
    definition = acrostic_poem.definition
    resource = ConversationResource(resource_constraint=definition.resource_constraint)
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


def test_format_resource():
    assert resource_phrase(1, ResourceConstraintUnit.TURNS) == "1 turn"
    assert resource_phrase(1, ResourceConstraintUnit.SECONDS) == "1 second"
    assert resource_phrase(1, ResourceConstraintUnit.MINUTES) == "1 minute"
    assert resource_phrase(2, ResourceConstraintUnit.TURNS) == "2 turns"
    assert resource_phrase(2, ResourceConstraintUnit.SECONDS) == "2 seconds"
    assert resource_phrase(2, ResourceConstraintUnit.MINUTES) == "2 minutes"
    assert resource_phrase(1.5, ResourceConstraintUnit.SECONDS) == "2 seconds"
    assert resource_phrase(1.5, ResourceConstraintUnit.MINUTES) == "2 minutes"
