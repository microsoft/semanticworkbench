from typing import cast

from skill_library.engine import RunContext
from skill_library.skills.posix import PosixSkill


async def run_command(context: RunContext, command: str) -> str:
    """
    Run a shell command in the current directory.
    """
    posix_skill = cast(PosixSkill, context.skills["posix"])
    shell = posix_skill.shell
    stdout, stderr = shell.run_command(command)
    return f"Command output:\n{stdout}\nCommand errors:\n{stderr}"


__default__ = run_command
