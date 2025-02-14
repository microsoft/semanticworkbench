from typing import Any, cast

from skill_library import AskUserFn, EmitFn, RunContext, RunRoutineFn
from skill_library.skills.posix import PosixSkill


async def main(
    context: RunContext, routine_state: dict[str, Any], emit: EmitFn, run: RunRoutineFn, ask_user: AskUserFn, path: str
) -> str:
    """
    Remove a file or directory.
    """
    posix_skill = cast(PosixSkill, context.skills["posix"])
    shell = posix_skill.shell
    shell.rm(path)
    return f"Removed {path}."
