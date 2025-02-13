# tst_skill/routines/a_routine.py
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


async def main(
    context: RunContext,
    ask_user: AskUserFn,
    print: PrintFn,
    run_action: RunActionFn,
    run_routine: RunRoutineFn,
    get_state: GetStateFn,
    set_state: SetStateFn,
    emit: EmitFn,
) -> str:
    # Call an action from the same skill
    await run_action("tst_skill.an_action")
    # Test asking user something
    response = await ask_user("test question")
    # Test printing something
    await print("test print")
    return response
