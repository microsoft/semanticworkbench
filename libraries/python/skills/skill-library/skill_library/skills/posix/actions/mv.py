from typing import cast

from skill_library.engine import RunContext
from skill_library.skills.posix import PosixSkill


async def mv(context: RunContext, src: str, dest: str) -> str:
    """
    Move a file or directory.
    """
    posix_skill = cast(PosixSkill, context.skills["posix"])
    shell = posix_skill.shell
    shell.mv(src, dest)
    return f"Moved {src} to {dest}."


__default__ = mv
