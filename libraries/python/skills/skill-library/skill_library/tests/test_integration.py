import pytest
from semantic_workbench_api_model.workbench_model import ConversationMessageList
from skill_library.engine import Engine
from skill_library.tests.tst_skill import TstSkill, TstSkillConfig


@pytest.fixture
async def engine():
    """Create an engine with our test skill"""

    async def get_history() -> ConversationMessageList:
        return ConversationMessageList(messages=[])

    engine = Engine(
        engine_id="test-id",
        message_history_provider=get_history,
        skills=[(TstSkill, TstSkillConfig(name="tst_skill"))],
    )
    await engine.start()
    return engine


@pytest.mark.asyncio
async def test_skill_registration(engine):
    """Test that skills are properly registered"""
    # Check if skill exists
    assert "tst_skill" in engine._skills

    # Check if routines were discovered
    routines = engine.list_routines()
    print("Available routines:", routines)
    assert "tst_skill.a_routine" in routines
