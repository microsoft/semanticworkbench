from typing import cast

from skill_library.engine import RunContext
from skill_library.skills.posix import PosixSkill


async def read_file(context: RunContext, filename: str) -> str:
    """
    Read the contents of a file.
    """
    posix_skill = cast(PosixSkill, context.skills["posix"])
    shell = posix_skill.shell
    return shell.read_file(filename)


__default__ = read_file
