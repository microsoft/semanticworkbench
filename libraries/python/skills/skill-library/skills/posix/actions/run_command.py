from skill_library.engine import RunContext


async def run_command(self, context: RunContext, command: str) -> str:
    """
    Run a shell command in the current directory.
    """
    shell = context.posix.skill.shell
    stdout, stderr = shell.run_command(command)
    return f"Command output:\n{stdout}\nCommand errors:\n{stderr}"
