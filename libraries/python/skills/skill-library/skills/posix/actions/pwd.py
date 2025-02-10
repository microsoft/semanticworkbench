from skill_library.engine import RunContext


async def pwd(self, context: RunContext) -> str:
    """
    Return the current directory.
    """
    shell = context.posix.skill.shell
    return shell.pwd()
