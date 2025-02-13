from typing import cast

from skill_library.engine import RunContext
from skill_library.skills.posix import PosixSkill


async def touch(context: RunContext, filename: str) -> str:
    """
    Create an empty file.
    """
    posix_skill = cast(PosixSkill, context.skills["posix"])
    shell = posix_skill.shell
    shell.touch(filename)
    return f"Created file {filename}."


__default__ = touch
