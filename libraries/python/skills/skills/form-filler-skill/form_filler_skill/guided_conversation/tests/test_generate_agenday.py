import pytest
from form_filler_skill.guided_conversation.agenda import Agenda
from form_filler_skill.guided_conversation.chat_drivers.update_agenda import generate_agenda
from form_filler_skill.guided_conversation.definitions import acrostic_poem
from form_filler_skill.guided_conversation.message import Conversation
from form_filler_skill.guided_conversation.resources import GCResource
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
