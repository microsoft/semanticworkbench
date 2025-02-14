from skill_library import RunContext
from skill_library.types import AskUserFn, EmitFn, GetStateFn, RunRoutineFn, SetStateFn


async def main(
    context: RunContext,
    ask_user: AskUserFn,
    run: RunRoutineFn,
    get_state: GetStateFn,
    set_state: SetStateFn,
    emit: EmitFn,
    username: str,
) -> None:
    await run("posix.cd", "/mnt/data")
    await run("posix.mkdir", username)
    await run("posix.cd", username)
    await run("posix.mkdir", "Documents")
    await run("posix.mkdir", "Downloads")
    await run("posix.mkdir", "Music")
    await run("posix.mkdir", "Pictures")
    await run("posix.mkdir", "Videos")
    await run("posix.cd", "/mnt/data")
    print(f"Home directory created for {username}.")
