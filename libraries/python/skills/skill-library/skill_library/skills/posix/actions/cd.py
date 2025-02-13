from typing import cast

from skill_library.engine import RunContext
from skill_library.skills.posix import PosixSkill


async def cd(context: RunContext, directory: str) -> str:
    """
    Change the current working directory.
    """
    posix_skill = cast(PosixSkill, context.skills["posix"])
    shell = posix_skill.shell
    try:
        shell.cd(directory)
        return f"Changed directory to {directory}."
    except FileNotFoundError:
        return f"Directory {directory} not found."


__default__ = cd
