from typing import cast

from skill_library.engine import RunContext
from skill_library.skills.posix import PosixSkill


async def ls(context: RunContext, path: str = ".") -> list[str]:
    """
    Change the current working directory.
    """
    posix_skill = cast(PosixSkill, context.skills["posix"])
    shell = posix_skill.shell
    return shell.ls(path)


__default__ = ls
