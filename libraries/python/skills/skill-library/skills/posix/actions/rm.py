from skill_library.engine import RunContext


async def rm(self, context: RunContext, path: str) -> str:
    """
    Remove a file or directory.
    """
    shell = context.posix.skill.shell
    shell.rm(path)
    return f"Removed {path}."
