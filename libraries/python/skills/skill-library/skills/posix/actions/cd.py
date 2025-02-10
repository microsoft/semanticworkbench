from skill_library.engine import RunContext


async def cd(self, context: RunContext, directory: str) -> str:
    """
    Change the current working directory.
    """
    shell = context.posix.skill.shell
    try:
        shell.cd(directory)
        return f"Changed directory to {directory}."
    except FileNotFoundError:
        return f"Directory {directory} not found."
