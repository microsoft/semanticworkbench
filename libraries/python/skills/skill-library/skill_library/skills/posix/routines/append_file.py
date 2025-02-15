from typing import Any, cast

from skill_library import AskUserFn, EmitFn, RunContext, RunRoutineFn
from skill_library.skills.posix import PosixSkill


async def main(
    context: RunContext,
    routine_state: dict[str, Any],
    emit: EmitFn,
    run: RunRoutineFn,
    ask_user: AskUserFn,
    filename: str,
    content: str,
) -> str:
    """
    Change the current working directory.
    """
    posix_skill = cast(PosixSkill, context.skills["posix"])
    shell = posix_skill.shell
    try:
        shell.append_file(filename, content)
        return f"Appended content to {filename}."
    except FileNotFoundError:
        return f"Filename {filename} not found."
