from typing import cast

from skill_library.engine import RunContext
from skill_library.skills.posix.posix_skill import PosixSkill


async def write_file(context: RunContext, filename: str, content: str) -> str:
    """
    Write content to a file.
    """
    posix_skill = cast(PosixSkill, context.skills["posix"])
    shell = posix_skill.shell
    shell.write_file(filename, content)
    return f"Wrote content to {filename}."


__default__ = write_file
