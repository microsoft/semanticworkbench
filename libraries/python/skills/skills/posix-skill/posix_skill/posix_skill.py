from pathlib import Path

from chat_driver import ChatDriverConfig
from context import ContextProtocol
from skill_library import InstructionRoutine, RoutineTypes, Skill

from .sandbox_shell import SandboxShell

NAME = "posix"
CLASS_NAME = "PosixSkill"
DESCRIPTION = "Manages the filesystem using a sand-boxed Posix shell."
DEFAULT_MAX_RETRIES = 3
INSTRUCTIONS = "You are an assistant that has access to a sand-boxed Posix shell."


class PosixSkill(Skill):
    def __init__(
        self,
        context: ContextProtocol,
        sandbox_dir: Path,
        chat_driver_config: ChatDriverConfig,
        mount_dir: str = "/mnt/data",
    ) -> None:
        self.shell = SandboxShell(sandbox_dir, mount_dir)

        # Put all functions in a group. We are going to use all these as (1)
        # skill actions, but also as (2) chat functions and (3) chat commands.
        # You can also put them in separate lists if you want to differentiate
        # between these.
        functions = [
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

        # Add some skill routines.
        routines: list[RoutineTypes] = [
            self.make_home_dir_routine(),
        ]

        # Re-configure the skill's chat driver.
        chat_driver_config.instructions = INSTRUCTIONS
        chat_driver_config.commands = functions
        chat_driver_config.functions = functions

        # Initialize the skill!
        super().__init__(
            name=NAME,
            description=DESCRIPTION,
            chat_driver_config=chat_driver_config,
            skill_actions=functions,
            routines=routines,
        )

    ##################################
    # Routines
    ##################################

    def make_home_dir_routine(self) -> InstructionRoutine:
        """Makes a home directory for the user."""
        return InstructionRoutine(
            "make_home_dir",
            "Create a home directory for the user.",
            routine=(
                "cd /mnt/data\n"
                "mkdir {{username}}\n"
                "cd {{username}}\n"
                "mkdir Documents\n"
                "mkdir Downloads\n"
                "mkdir Music\n"
                "mkdir Pictures\n"
                "mkdir Videos\n"
            ),
            skill=self,
        )

    ##################################
    # Actions
    ##################################

    def cd(self, context: ContextProtocol, directory: str) -> str:
        """
        Change the current working directory.
        """
        try:
            self.shell.cd(directory)
            return f"Changed directory to {directory}."
        except FileNotFoundError:
            return f"Directory {directory} not found."

    def ls(self, context: ContextProtocol, path: str = ".") -> list[str]:
        """
        List directory contents.
        """
        return self.shell.ls(path)

    def touch(self, context: ContextProtocol, filename: str) -> str:
        """
        Create an empty file.
        """
        self.shell.touch(filename)
        return f"Created file {filename}."

    def mkdir(self, context: ContextProtocol, dirname: str) -> str:
        """
        Create a new directory.
        """
        self.shell.mkdir(dirname)
        return f"Created directory {dirname}."

    def mv(self, context: ContextProtocol, src: str, dest: str) -> str:
        """
        Move a file or directory.
        """
        self.shell.mv(src, dest)
        return f"Moved {src} to {dest}."

    def rm(self, context: ContextProtocol, path: str) -> str:
        """
        Remove a file or directory.
        """
        self.shell.rm(path)
        return f"Removed {path}."

    def pwd(self, context: ContextProtocol) -> str:
        """
        Return the current directory.
        """
        return self.shell.pwd()

    def run_command(self, context: ContextProtocol, command: str) -> str:
        """
        Run a shell command in the current directory.
        """
        stdout, stderr = self.shell.run_command(command)
        return f"Command output:\n{stdout}\nCommand errors:\n{stderr}"

    def read_file(self, context: ContextProtocol, filename: str) -> str:
        """
        Read the contents of a file.
        """
        return self.shell.read_file(filename)

    def write_file(self, context: ContextProtocol, filename: str, content: str) -> str:
        """
        Write content to a file.
        """
        self.shell.write_file(filename, content)
        return f"Wrote content to {filename}."
