from skill_library.engine import RunContext


async def ls(self, context: RunContext, path: str = ".") -> str:
    """
    Change the current working directory.
    """
    shell = context.posix.skill.shell
    return shell.ls(path)
