from skill_library.engine import RunContext


async def touch(self, context: RunContext, filename: str) -> str:
    """
    Create an empty file.
    """
    shell = context.posix.skill.shell
    shell.touch(filename)
    return f"Created file {filename}."
