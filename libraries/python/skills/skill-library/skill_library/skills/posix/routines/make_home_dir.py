from typing import Any

from skill_library import AskUserFn, EmitFn, RunContext, RunRoutineFn


async def main(
    context: RunContext,
    routine_state: dict[str, Any],
    emit: EmitFn,
    run: RunRoutineFn,
    ask_user: AskUserFn,
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
