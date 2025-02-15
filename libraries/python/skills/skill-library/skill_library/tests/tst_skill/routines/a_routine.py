# tst_skill/routines/a_routine.py
from typing import Any

from skill_library.types import (
    AskUserFn,
    EmitFn,
    RunContext,
    RunRoutineFn,
)


async def main(
    context: RunContext,
    routine_state: dict[str, Any],
    emit: EmitFn,
    run: RunRoutineFn,
    ask_user: AskUserFn,
) -> str:
    # Call an action from the same skill
    await run("tst_skill.an_action")
    # Test asking user something
    response = await ask_user("test question")
    return response
