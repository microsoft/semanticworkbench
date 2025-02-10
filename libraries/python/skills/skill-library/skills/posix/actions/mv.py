from skill_library.engine import RunContext


async def mv(self, context: RunContext, src: str, dest: str) -> str:
    """
    Move a file or directory.
    """
    shell = context.posix.skill.shell
    shell.mv(src, dest)
    return f"Moved {src} to {dest}."
