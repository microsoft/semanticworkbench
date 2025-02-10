from skill_library.engine import RunContext


async def write_file(self, context: RunContext, filename: str, content: str) -> str:
    """
    Write content to a file.
    """
    shell = context.posix.skill.shell
    shell.write_file(filename, content)
    return f"Wrote content to {filename}."
