import asyncio

import pytest
from events import InformationEvent, MessageEvent, StatusUpdatedEvent
from semantic_workbench_api_model.workbench_model import ConversationMessageList
from skill_library.engine import Engine
from skill_library.types import (
    AskUserFn,
    EmitFn,
    GetStateFn,
    PrintFn,
    RunActionFn,
    RunContext,
    RunRoutineFn,
    SetStateFn,
)
from tst_skill import TstSkill, TstSkillConfig


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

    yield engine

    # Cleanup
    await engine.clear(include_drives=True)
    if engine._routine_output_futures:
        engine._routine_output_futures.clear()


@pytest.mark.asyncio
async def test_nested_routines(engine):
    """Test that a routine can call another routine and handle nested user interaction"""

    # Add a subroutine that asks a question
    async def subroutine(
        context: RunContext,
        ask_user: AskUserFn,
        print: PrintFn,
        run_action: RunActionFn,
        run_routine: RunRoutineFn,
        get_state: GetStateFn,
        set_state: SetStateFn,
        emit: EmitFn,
    ):
        response = await ask_user("subroutine question")
        await print("subroutine received: " + response)
        return "subroutine complete: " + response

    # Add a parent routine that calls the subroutine
    async def parent_routine(
        context: RunContext,
        ask_user: AskUserFn,
        print: PrintFn,
        run_action: RunActionFn,
        run_routine: RunRoutineFn,
        get_state: GetStateFn,
        set_state: SetStateFn,
        emit: EmitFn,
    ):
        await print("parent starting")
        first_response = await ask_user("parent question 1")

        # Call subroutine
        sub_result = await run_routine("tst_skill.subroutine")

        second_response = await ask_user("parent question 2")
        await print(f"parent got: {first_response}, {sub_result}, {second_response}")
        return "parent complete"

    # Register the test routines
    engine._skills["tst_skill"]._routines["subroutine"] = subroutine
    engine._skills["tst_skill"]._routines["parent_routine"] = parent_routine

    # Start the parent routine
    routine_task = asyncio.create_task(engine.run_routine("tst_skill.parent_routine"))

    async def get_next_non_status_event():
        """Helper to skip past status events"""
        while True:
            event = await asyncio.wait_for(engine._event_queue.get(), timeout=1.0)
            if not isinstance(event, StatusUpdatedEvent):
                return event

    try:
        # Parent routine starts
        event = await get_next_non_status_event()
        assert isinstance(event, InformationEvent)
        assert event.message == "parent starting"

        # Parent asks first question
        event = await get_next_non_status_event()
        assert isinstance(event, MessageEvent)
        assert event.message == "parent question 1"
        await engine.resume_routine("parent answer 1")

        # Subroutine asks question
        event = await get_next_non_status_event()
        assert isinstance(event, MessageEvent)
        assert event.message == "subroutine question"
        await engine.resume_routine("sub answer")

        # Subroutine prints response
        event = await get_next_non_status_event()
        assert isinstance(event, InformationEvent)
        assert event.message == "subroutine received: sub answer"

        # Subroutine completes
        event = await get_next_non_status_event()
        assert isinstance(event, InformationEvent)
        assert event.message == "subroutine complete: sub answer"

        # Parent asks second question
        event = await get_next_non_status_event()
        assert isinstance(event, MessageEvent)
        assert event.message == "parent question 2"
        await engine.resume_routine("parent answer 2")

        # Parent prints final summary
        event = await get_next_non_status_event()
        assert isinstance(event, InformationEvent)
        assert event.message == "parent got: parent answer 1, subroutine complete: sub answer, parent answer 2"

        # Get final result
        result = await asyncio.wait_for(routine_task, timeout=1.0)
        assert result == "parent complete"

    except asyncio.TimeoutError:
        routine_task.cancel()
        try:
            await routine_task
        except asyncio.CancelledError:
            pass
        raise
    except Exception as e:
        if not routine_task.done():
            routine_task.cancel()
            try:
                await routine_task
            except asyncio.CancelledError:
                pass
        else:
            exc = routine_task.exception()
            if exc:
                raise exc from e
        raise


@pytest.mark.asyncio
async def test_deeply_nested_routines(engine):
    """Test that routines can be nested multiple levels deep"""

    async def level3_routine(
        context: RunContext,
        ask_user: AskUserFn,
        print: PrintFn,
        run_action: RunActionFn,
        run_routine: RunRoutineFn,
        get_state: GetStateFn,
        set_state: SetStateFn,
        emit: EmitFn,
    ):
        response = await ask_user("level 3 question")
        return f"level3: {response}"

    async def level2_routine(
        context: RunContext,
        ask_user: AskUserFn,
        print: PrintFn,
        run_action: RunActionFn,
        run_routine: RunRoutineFn,
        get_state: GetStateFn,
        set_state: SetStateFn,
        emit: EmitFn,
    ):
        response = await ask_user("level 2 question")
        level3_result = await (await run_routine("tst_skill.level3_routine"))
        return f"level2: {response}, {level3_result}"

    async def level1_routine(
        context: RunContext,
        ask_user: AskUserFn,
        print: PrintFn,
        run_action: RunActionFn,
        run_routine: RunRoutineFn,
        get_state: GetStateFn,
        set_state: SetStateFn,
        emit: EmitFn,
    ):
        response = await ask_user("level 1 question")
        level2_result = await (await run_routine("tst_skill.level2_routine"))
        return f"level1: {response}, {level2_result}"

    # Register the test routines
    engine._skills["tst_skill"]._routines["level1_routine"] = level1_routine
    engine._skills["tst_skill"]._routines["level2_routine"] = level2_routine
    engine._skills["tst_skill"]._routines["level3_routine"] = level3_routine

    # Start the top-level routine
    routine_task = asyncio.create_task(engine.run_routine("tst_skill.level1_routine"))

    try:
        # Level 1 question
        event = await asyncio.wait_for(engine._event_queue.get(), timeout=1.0)
        assert isinstance(event, MessageEvent)
        assert event.message == "level 1 question"
        await engine.resume_routine("answer 1")

        # Level 2 question
        event = await asyncio.wait_for(engine._event_queue.get(), timeout=1.0)
        assert isinstance(event, MessageEvent)
        assert event.message == "level 2 question"
        await engine.resume_routine("answer 2")

        # Level 3 question
        event = await asyncio.wait_for(engine._event_queue.get(), timeout=1.0)
        assert isinstance(event, MessageEvent)
        assert event.message == "level 3 question"
        await engine.resume_routine("answer 3")

        # Get final result
        result = await asyncio.wait_for(routine_task, timeout=1.0)
        assert await result == "level1: answer 1, level2: answer 2, level3: answer 3"

    except asyncio.TimeoutError:
        routine_task.cancel()
        try:
            await routine_task
        except asyncio.CancelledError:
            pass
        raise
    except Exception as e:
        if not routine_task.done():
            routine_task.cancel()
            try:
                await routine_task
            except asyncio.CancelledError:
                pass
        else:
            exc = routine_task.exception()
            if exc:
                raise exc from e
        raise
