from pathlib import Path

from semantic_workbench_api_model.workbench_model import ConversationMessageList
from skill_library.engine import Engine
from skill_library.skills.posix.posix_skill import PosixSkill, PosixSkillConfig


def test_common_posix_skill_initialization():
    engine_id = "test-1"

    async def get_history() -> ConversationMessageList:
        return ConversationMessageList(messages=[])

    engine = Engine(
        engine_id="test-1",
        message_history_provider=get_history,
        skills=[
            (
                PosixSkill,
                PosixSkillConfig(
                    name="posix",
                    sandbox_dir=Path(".data") / engine_id,
                    mount_dir="/mnt/data",
                ),
            ),
        ],
    )

    try:
        actions = engine.list_actions()
    except Exception as e:
        assert False, f"Error listing actions: {e}"

    assert "posix.ls" in actions

    routines = engine.list_routines()
    assert "posix.make_home_dir" in routines
