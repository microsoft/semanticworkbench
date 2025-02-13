from typing import cast

from skill_library.engine import RunContext
from skill_library.skills.posix import PosixSkill


async def mkd_dir(context: RunContext, dirname: str) -> str:
    """
    Create a new directory.
    """
    posix_skill = cast(PosixSkill, context.skills["posix"])
    shell = posix_skill.shell
    shell.mkdir(dirname)
    return f"Created directory {dirname}."


__default__ = mkd_dir
