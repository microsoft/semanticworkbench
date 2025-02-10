import asyncio

import pytest
from semantic_workbench_api_model.workbench_model import ConversationMessageList
from skill_library.engine.engine import Engine
from tst_skill import TstSkill, TstSkillConfig


@pytest.fixture
async def engine():
    """Create an engine with our test skill"""

    async def get_history() -> ConversationMessageList:
        return ConversationMessageList(messages=[])

    engine = Engine(
        name="test",
        engine_id="test-id",
        message_history_provider=get_history,
        skills=[(TstSkill, TstSkillConfig(skill_name="tst_skill", counter=0))],
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

    # Check if actions were discovered
    actions = engine.list_actions()
    print("Available actions:", actions)
    assert "tst_skill.an_action" in actions


@pytest.mark.asyncio
async def test_run_simple_routine(engine):
    """Test running a very simple routine that doesn't use ask_user"""

    # Add a simple test routine directly for debugging
    async def simple_test(run_context, ask_user, print):
        return "test complete"

    engine._skills["tst_skill"]._routines["simple_test"] = simple_test

    result = await engine.run_routine("tst_skill.simple_test")
    assert result == "test complete"


@pytest.mark.asyncio
async def test_engine_runs_routine(engine):
    """Test that engine can run a routine and handle user interaction"""

    # Start the routine with exception handling
    routine_task = asyncio.create_task(engine.run_routine("tst_skill.a_routine"))

    try:
        # Wait for and verify the question was asked
        event = await asyncio.wait_for(engine._event_queue.get(), timeout=1.0)
        assert event.message == "test question"

        # Simulate user response
        await engine.resume_routine("test response")

        # Wait for and verify print message
        event = await asyncio.wait_for(engine._event_queue.get(), timeout=1.0)
        assert event.message == "test print"

        # Get routine result
        result = await asyncio.wait_for(routine_task, timeout=1.0)
        assert result == "test response"

    except asyncio.TimeoutError:
        # Cancel the task if we time out
        routine_task.cancel()
        try:
            await routine_task
        except asyncio.CancelledError:
            pass
        raise
    except Exception as e:
        # If the task failed, get its exception
        if not routine_task.done():
            routine_task.cancel()
            try:
                await routine_task
            except asyncio.CancelledError:
                pass
        else:
            # Re-raise the task's exception if it had one
            exc = routine_task.exception()
            if exc:
                raise exc from e
        raise
