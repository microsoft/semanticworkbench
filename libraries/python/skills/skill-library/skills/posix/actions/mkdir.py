from skill_library.engine import RunContext


async def mkdir(self, context: RunContext, dirname: str) -> str:
    """
    Create a new directory.
    """
    shell = context.posix.skill.shell
    shell.mkdir(dirname)
    return f"Created directory {dirname}."
