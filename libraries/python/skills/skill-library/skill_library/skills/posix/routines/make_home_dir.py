from skill_library import RunContext
from skill_library.types import AskUserFn, EmitFn, GetStateFn, PrintFn, RunActionFn, RunRoutineFn, SetStateFn


async def main(
    context: RunContext,
    ask_user: AskUserFn,
    print: PrintFn,
    run_action: RunActionFn,
    run_routine: RunRoutineFn,
    get_state: GetStateFn,
    set_state: SetStateFn,
    emit: EmitFn,
    username: str,
) -> None:
    await run_action("posix.cd", "/mnt/data")
    await run_action("posix.mkdir", username)
    await run_action("posix.cd", username)
    await run_action("posix.mkdir", "Documents")
    await run_action("posix.mkdir", "Downloads")
    await run_action("posix.mkdir", "Music")
    await run_action("posix.mkdir", "Pictures")
    await run_action("posix.mkdir", "Videos")
    await run_action("posix.cd", "/mnt/data")
    print(f"Home directory created for {username}.")
