from skill_library.engine import RunContext


async def read_file(self, context: RunContext, filename: str) -> str:
    """
    Read the contents of a file.
    """
    shell = context.posix.skill.shell
    return shell.read_file(filename)
