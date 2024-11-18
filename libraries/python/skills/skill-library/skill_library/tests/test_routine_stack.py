from assistant_drive import Drive, DriveConfig, IfDriveFileExistsBehavior
from skill_library.routine_stack import RoutineStack


async def test_routine_stack():
    drive = Drive(
        DriveConfig(
            root=".data/test", default_if_exists_behavior=IfDriveFileExistsBehavior.OVERWRITE
        )
    )
    stack = RoutineStack(drive)

    await stack.clear()

    # Test push
    frame_id = await stack.push("test")
    assert frame_id

    # Get
    frames = await stack.get()
    assert frames
    assert len(frames) == 1
    assert frames[0].id == frame_id

    # Test peek
    frame = await stack.peek()
    assert frame
    assert frame.id == frame_id
    assert frame.state == {}

    # Test set_current_state_key
    await stack.set_current_state_key("test", "value")
    value = await stack.get_current_state_key("test")
    assert value == "value"

    # Test get_current_state
    state = await stack.get_current_state()
    assert state
    assert state["test"] == "value"

    # Test set_current_state
    new_state = {"new": "state"}
    await stack.set_current_state(new_state)
    state = await stack.get_current_state()
    assert state
    assert state == new_state

    # Test pop
    frame = await stack.pop()
    assert frame
    assert frame.id == frame_id
    assert await stack.length() == 0

    # Test pop empty
    frame = await stack.pop()
    assert not frame
