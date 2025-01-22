from pathlib import Path
from textwrap import dedent

from openai_client.chat_driver import ChatDriverConfig
from skill_library import (
    ActionCallable,
    ChatDriverFunctions,
    InstructionRoutine,
    RoutineTypes,
    RunContext,
    RunContextProvider,
    Skill,
    SkillDefinition,
)

from .sandbox_shell import SandboxShell

NAME = "posix"
CLASS_NAME = "PosixSkill"
DESCRIPTION = "Manages the filesystem using a sand-boxed Posix shell."
DEFAULT_MAX_RETRIES = 3
INSTRUCTIONS = "You are an assistant that has access to a sand-boxed Posix shell."


class PosixSkill(Skill):
    def __init__(
        self,
        skill_definition: "PosixSkillDefinition",
        run_context_provider: RunContextProvider,
    ) -> None:
        self.shell = SandboxShell(skill_definition.sandbox_dir, skill_definition.mount_dir)

        # Define action
        action_functions: list[ActionCallable] = [
            self.cd,
            self.ls,
            self.touch,
            self.mkdir,
            self.mv,
            self.rm,
            self.pwd,
            self.run_command,
            self.read_file,
            self.write_file,
        ]

        # Add skill routines.
        routines: list[RoutineTypes] = [
            self.make_home_dir_routine(skill_definition.name),
        ]

        # Add commands and functions to the skill's chat driver.
        if skill_definition.chat_driver_config:
            # Go ahead and make all actions available.
            chat_driver_commands = ChatDriverFunctions(action_functions, run_context_provider).all()
            chat_driver_functions = ChatDriverFunctions(action_functions, run_context_provider).all()
            skill_definition.chat_driver_config.instructions = INSTRUCTIONS
            skill_definition.chat_driver_config.commands = chat_driver_commands
            skill_definition.chat_driver_config.functions = chat_driver_functions

        # Initialize the skill!
        super().__init__(
            skill_definition=skill_definition,
            run_context_provider=run_context_provider,
            actions=action_functions,
            routines=routines,
        )

    ##################################
    # Routines
    ##################################

    def make_home_dir_routine(self, skill_name: str) -> InstructionRoutine:
        """Makes a home directory for the user."""
        return InstructionRoutine(
            "make_home_dir",
            skill_name,
            "Create a home directory for the user.",
            routine=dedent("""
                cd /mnt/data
                mkdir {{username}}
                cd {{username}}
                mkdir Documents
                mkdir Downloads
                mkdir Music
                mkdir Pictures
                mkdir Videos
                cd /mnt/data
            """),
        )

    ##################################
    # Actions
    ##################################

    def cd(self, run_context: RunContext, directory: str) -> str:
        """
        Change the current working directory.
        """
        try:
            self.shell.cd(directory)
            return f"Changed directory to {directory}."
        except FileNotFoundError:
            return f"Directory {directory} not found."

    def ls(self, run_context: RunContext, path: str = ".") -> list[str]:
        """
        List directory contents.
        """
        return self.shell.ls(path)

    def touch(self, run_context: RunContext, filename: str) -> str:
        """
        Create an empty file.
        """
        self.shell.touch(filename)
        return f"Created file {filename}."

    def mkdir(self, run_context: RunContext, dirname: str) -> str:
        """
        Create a new directory.
        """
        self.shell.mkdir(dirname)
        return f"Created directory {dirname}."

    def mv(self, run_context: RunContext, src: str, dest: str) -> str:
        """
        Move a file or directory.
        """
        self.shell.mv(src, dest)
        return f"Moved {src} to {dest}."

    def rm(self, run_context: RunContext, path: str) -> str:
        """
        Remove a file or directory.
        """
        self.shell.rm(path)
        return f"Removed {path}."

    def pwd(self, run_context: RunContext) -> str:
        """
        Return the current directory.
        """
        return self.shell.pwd()

    def run_command(self, run_context: RunContext, command: str) -> str:
        """
        Run a shell command in the current directory.
        """
        stdout, stderr = self.shell.run_command(command)
        return f"Command output:\n{stdout}\nCommand errors:\n{stderr}"

    def read_file(self, run_context: RunContext, filename: str) -> str:
        """
        Read the contents of a file.
        """
        return self.shell.read_file(filename)

    def write_file(self, run_context: RunContext, filename: str, content: str) -> str:
        """
        Write content to a file.
        """
        self.shell.write_file(filename, content)
        return f"Wrote content to {filename}."


class PosixSkillDefinition(SkillDefinition):
    def __init__(
        self,
        name: str,
        sandbox_dir: Path,
        mount_dir: str = "/mnt/data",
        description: str | None = None,
        chat_driver_config: ChatDriverConfig | None = None,
    ) -> None:
        self.name = name
        self.description = description or DESCRIPTION
        self.sandbox_dir = sandbox_dir
        self.mount_dir = mount_dir
        self.chat_driver_config = chat_driver_config
        self.skill_class = PosixSkill
