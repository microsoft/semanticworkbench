from typing import cast

from skill_library.engine import RunContext
from skill_library.skills.posix import PosixSkill


async def pwd(context: RunContext) -> str:
    """
    Return the current directory.
    """
    posix_skill = cast(PosixSkill, context.skills["posix"])
    shell = posix_skill.shell
    return shell.pwd()


__default__ = pwd
