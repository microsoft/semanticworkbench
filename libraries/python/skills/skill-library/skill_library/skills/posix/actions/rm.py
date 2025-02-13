from typing import cast

from skill_library.engine import RunContext
from skill_library.skills.posix import PosixSkill


async def rm(context: RunContext, path: str) -> str:
    """
    Remove a file or directory.
    """
    posix_skill = cast(PosixSkill, context.skills["posix"])
    shell = posix_skill.shell
    shell.rm(path)
    return f"Removed {path}."


__default__ = rm
