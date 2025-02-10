from skill_library.engine import RunContext


async def cd(self, context: RunContext, filename: str, content: str) -> str:
    """
    Change the current working directory.
    """
    shell = context.posix.skill.shell
    try:
        shell.append_file(filename, content)
        return f"Appended content to {filename}."
    except FileNotFoundError:
        return f"Filename {filename} not found."
