import os
from pathlib import Path
import shutil
import subprocess


class SandboxShell:
    def __init__(self, sandbox_dir: Path, mount_dir: str = "/mnt/data") -> None:
        self.sandbox_dir = os.path.abspath(sandbox_dir)
        self.mount_dir = mount_dir
        os.makedirs(self.sandbox_dir, exist_ok=True)
        self.current_dir = self.sandbox_dir

    def _resolve_path(self, path) -> str:
        """Resolve the given path within the sandbox."""

        # If the path is a mount path, return the corresponding sandbox path.
        if path.startswith(self.mount_dir):
            return os.path.join(self.sandbox_dir, path[len(self.mount_dir) :].lstrip("/"))

        # If the path is relative, join it with the current directory.
        if not os.path.isabs(path):
            path = os.path.join(self.current_dir, path)

        # Resolve the absolute path.
        abs_path = os.path.abspath(os.path.join(self.current_dir, path))

        # Prevent access outside the sandbox directory.
        if not abs_path.startswith(self.sandbox_dir):
            raise ValueError("Access outside the sandbox directory is not allowed")
        return abs_path

    def cd(self, path) -> None:
        """Change the current directory."""
        new_dir = self._resolve_path(path)
        if not os.path.isdir(new_dir):
            raise FileNotFoundError(f"No such directory: {path}")
        self.current_dir = new_dir

    def ls(self, path=".") -> list[str]:
        """List directory contents."""
        target_dir = self._resolve_path(path)
        return os.listdir(target_dir)

    def touch(self, filename) -> None:
        """Create an empty file."""
        filepath = self._resolve_path(filename)
        with open(filepath, "a"):
            os.utime(filepath, None)

    def mkdir(self, dirname) -> None:
        """Create a new directory."""
        dirpath = self._resolve_path(dirname)
        os.makedirs(dirpath, exist_ok=True)

    def mv(self, src, dest) -> None:
        """Move a file or directory."""
        src_path = self._resolve_path(src)
        dest_path = self._resolve_path(dest)
        shutil.move(src_path, dest_path)

    def rm(self, path) -> None:
        """Remove a file or directory."""
        target_path = self._resolve_path(path)
        if os.path.isdir(target_path):
            shutil.rmtree(target_path)
        else:
            os.remove(target_path)

    def pwd(self) -> str:
        """Return the current directory."""
        return self.current_dir

    def run_command(self, command) -> tuple[str, str]:
        """Run a shell command in the current directory."""
        result = subprocess.run(
            command, shell=True, cwd=self.current_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return result.stdout.decode(), result.stderr.decode()

    def read_file(self, filename) -> str:
        """Read the contents of a file."""
        filepath = self._resolve_path(filename)
        with open(filepath, "r") as f:
            return f.read()

    def write_file(self, filename, content) -> None:
        """Write content to a file."""
        filepath = self._resolve_path(filename)
        with open(filepath, "w") as f:
            f.write(content)
