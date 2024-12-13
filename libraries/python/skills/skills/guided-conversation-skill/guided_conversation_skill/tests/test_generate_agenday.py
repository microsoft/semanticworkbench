import pytest
from guided_conversation_skill.agenda import Agenda
from guided_conversation_skill.chat_completions.update_agenda import generate_agenda
from guided_conversation_skill.conversation_guides import acrostic_poem
from guided_conversation_skill.message import Conversation
from guided_conversation_skill.resources import GCResource
from skill_library.types import LanguageModel


@pytest.mark.skip("For manual testing.")
async def test_generage_agenda(client: LanguageModel) -> None:
    conversation = Conversation().add_user_message("Hi!")
    agenda = Agenda()
    artifact = {}
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
