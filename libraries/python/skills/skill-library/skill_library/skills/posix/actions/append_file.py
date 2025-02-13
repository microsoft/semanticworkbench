from typing import cast

from skill_library.engine import RunContext
from skill_library.skills.posix import PosixSkill


async def append_file(context: RunContext, filename: str, content: str) -> str:
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


__default__ = append_file
