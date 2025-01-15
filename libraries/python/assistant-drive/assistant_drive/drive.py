import io
import json
import pathlib
from contextlib import contextmanager
from datetime import datetime
from enum import StrEnum
from os import PathLike
from typing import Any, BinaryIO, Iterator

from pydantic import BaseModel


class IfDriveFileExistsBehavior(StrEnum):
    FAIL = "fail"
    OVERWRITE = "overwrite"
    AUTO_RENAME = "auto_rename"


class DriveConfig(BaseModel):
    root: str | PathLike
    default_if_exists_behavior: IfDriveFileExistsBehavior = IfDriveFileExistsBehavior.OVERWRITE


class FileMetadata:
    def __init__(self, filename: str, dir: str | None, content_type: str, size: int) -> None:
        self.filename = filename
        self.dir = dir
        self.content_type = content_type
        self.size = size
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "dir": self.dir,
            "content_type": self.content_type,
            "size": self.size,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @staticmethod
    def from_dict(data: dict) -> "FileMetadata":
        metadata = FileMetadata(
            filename=data["filename"],
            dir=data["dir"],
            content_type=data["content_type"],
            size=data["size"],
        )
        metadata.created_at = datetime.fromisoformat(data["created_at"])
        metadata.updated_at = datetime.fromisoformat(data["updated_at"])
        return metadata


class Drive:
    def __init__(self, config: DriveConfig) -> None:
        self.root_path = pathlib.Path(config.root)
        self.default_if_exists_behavior = config.default_if_exists_behavior

    def _path_for(self, filename: str | None = None, dir: str | None = None) -> pathlib.Path:
        """Return the actual path for a dir/file combo, creating the dir as needed."""
        namespace_path = self.root_path / (dir or "")
        namespace_path.mkdir(parents=True, exist_ok=True)
        if filename is None:
            return namespace_path
        return namespace_path / filename

    def _metadata_dir_for(self, filename: str, dir: str | None = None) -> pathlib.Path:
        """Return the metadata directory path for a file."""
        file_path = self._path_for(filename, dir)
        return file_path.parent / (file_path.name + ".metadata")

    def _metadata_file_path(self, filename: str, dir: str | None = None) -> pathlib.Path:
        """Return the path to the metadata.json file for a given file."""
        metadata_dir = self._metadata_dir_for(filename, dir)
        return metadata_dir / "metadata.json"

    def _write_metadata(self, metadata: FileMetadata) -> None:
        """Write metadata to the appropriate metadata directory."""
        metadata_dir = self._metadata_dir_for(metadata.filename, metadata.dir)
        metadata_dir.mkdir(parents=True, exist_ok=True)

        metadata_file = metadata_dir / "metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata.to_dict(), f, indent=2)

    def _read_metadata(self, filename: str, dir: str | None = None) -> FileMetadata:
        """Read metadata from the metadata directory."""
        metadata_file = self._metadata_file_path(filename, dir)
        if not metadata_file.exists():
            raise FileNotFoundError(f"No metadata found for {filename}")

        with open(metadata_file, "r") as f:
            data = json.load(f)
            return FileMetadata.from_dict(data)

    #########################
    # Drive methods.
    #########################

    def subdrive(self, dir: str | pathlib.Path) -> "Drive":
        """Create a new Drive instance for a subdirectory of this drive.

        Args:
            dir: The subdirectory path relative to this drive's root

        Returns:
            A new Drive instance with its root at the specified subdirectory
        """
        new_root = self.root_path / dir
        config = DriveConfig(root=new_root, default_if_exists_behavior=self.default_if_exists_behavior)
        return Drive(config)

    def delete_drive(self) -> None:
        """Delete the entire drive directory and all its contents.

        This is a destructive operation that will delete all files and metadata
        in the drive. Use with caution.

        Raises:
            ValueError: If the drive's root path is a system directory (e.g., '/' or '/home')
        """
        # Basic safety check to prevent accidental deletion of system directories
        root_path = self.root_path.absolute()
        suspicious_paths = [
            pathlib.Path("/"),
            pathlib.Path("/home"),
            pathlib.Path("/usr"),
            pathlib.Path("/etc"),
            pathlib.Path("/var"),
            pathlib.Path("/tmp"),
            pathlib.Path("C:\\"),
            pathlib.Path("C:"),
            pathlib.Path("/Users"),
        ]
        if root_path in suspicious_paths:
            raise ValueError(f"Refusing to delete system directory: {root_path}")

        if self.root_path.exists():
            import shutil

            shutil.rmtree(self.root_path)

    #########################
    # File methods.
    #########################

    def write(
        self,
        content: BinaryIO,
        filename: str,
        dir: str | None = None,
        if_exists: IfDriveFileExistsBehavior | None = None,
    ) -> FileMetadata:
        """Write a file and its metadata."""
        if if_exists is None:
            if_exists = self.default_if_exists_behavior

        if self.file_exists(filename, dir):
            if if_exists == IfDriveFileExistsBehavior.FAIL:
                raise FileExistsError(f"File {filename} already exists")
            elif if_exists == IfDriveFileExistsBehavior.AUTO_RENAME:
                base, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
                counter = 1
                while self.file_exists(filename, dir):
                    filename = f"{base}({counter}).{ext}" if ext else f"{base}({counter})"
                    counter += 1

        # Get current position in stream
        pos = content.tell()

        # Create metadata
        content.seek(0, 2)  # Seek to end to get size
        size = content.tell()
        content.seek(0)  # Reset to beginning

        metadata = FileMetadata(filename=filename, dir=dir, content_type=self._guess_content_type(filename), size=size)

        # Write the file
        file_path = self._path_for(filename, dir)
        with open(file_path, "wb") as f:
            f.write(content.read())

        # Write metadata
        self._write_metadata(metadata)

        # Restore stream position
        content.seek(pos)
        return metadata

    def delete(self, filename: str, dir: str | None = None) -> None:
        """Delete a file and its metadata directory."""
        file_path = self._path_for(filename, dir)
        metadata_dir = self._metadata_dir_for(filename, dir)

        if file_path.exists():
            file_path.unlink()
        if metadata_dir.exists():
            import shutil

            shutil.rmtree(metadata_dir)

    @contextmanager
    def open_file(self, filename: str, dir: str | None = None) -> Iterator[BinaryIO]:
        """Open a file for reading."""
        file_path = self._path_for(filename, dir)
        if not file_path.exists():
            raise FileNotFoundError(f"File {filename} not found")

        with open(file_path, "rb") as f:
            yield f

    def get_metadata(self, filename: str, dir: str | None = None) -> FileMetadata:
        """Get metadata for a file."""
        return self._read_metadata(filename, dir)

    def file_exists(self, filename: str, dir: str | None = None) -> bool:
        """Check if a file exists."""
        return self._path_for(filename, dir).exists()

    def _guess_content_type(self, filename: str) -> str:
        """Guess the content type of a file based on its extension."""
        import mimetypes

        content_type, _ = mimetypes.guess_type(filename)
        return content_type or "application/octet-stream"

    def list(self, dir: str = "") -> Iterator[str]:
        """List all files and directories in a directory (non-recursively).

        Args:
            dir: The directory to list files from. Defaults to root directory.

        Returns:
            Iterator of names (without paths) of files and directories that contain files.
            Excludes empty directories and metadata directories.
        """
        dir_path = self._path_for(dir=dir)
        if not dir_path.is_dir():
            return

        for path in dir_path.iterdir():
            # Skip metadata directories
            if path.name.endswith(".metadata"):
                continue

            if path.is_file():
                yield path.name
            elif path.is_dir():
                # Include directory if it contains any non-metadata files or non-empty directories
                has_content = False
                for subpath in path.rglob("*"):
                    if subpath.is_file() and not any(p.name.endswith(".metadata") for p in subpath.parents):
                        has_content = True
                        break
                if has_content:
                    yield path.name

    #########################
    # Pydantic model methods.
    #########################

    from typing import TypeVar

    ModelT = TypeVar("ModelT", bound=BaseModel)

    def write_model(
        self,
        value: BaseModel,
        filename: str,
        dir: str | None = None,
        serialization_context: dict[str, Any] | None = None,
        if_exists: IfDriveFileExistsBehavior | None = None,
    ) -> None:
        """Write a pydantic model to a file.

        Args:
            value: The Pydantic model to write
            filename: Name of the file to write to
            dir: Optional directory path relative to drive root
            serialization_context: Optional context dict passed to model_dump_json
            if_exists: How to handle existing files. Uses drive default if not specified.
        """
        data_json = value.model_dump_json(context=serialization_context)
        data_bytes = data_json.encode("utf-8")
        self.write(io.BytesIO(data_bytes), filename, dir, if_exists)

    def read_model(
        self, cls: type[ModelT], filename: str, dir: str | None = None, strict: bool | None = None
    ) -> ModelT:
        """Read a pydantic model from a file.

        Args:
            cls: The Pydantic model class to deserialize into
            filename: Name of the file to read from
            dir: Optional directory path relative to drive root
            strict: Whether to use strict validation. Default is None (use model's settings)

        Returns:
            An instance of the specified model class

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValidationError: If the file content can't be parsed into the model
        """
        with self.open_file(filename, dir) as f:
            data_json = f.read().decode("utf-8")
        return cls.model_validate_json(data_json, strict=strict)

    def read_models(
        self,
        cls: type[ModelT],
        dir: str | None = None,
    ) -> Iterator[ModelT]:
        """Read all Pydantic models from files in a directory.

        Args:
            cls: The Pydantic model class to deserialize into
            dir: Optional directory path relative to drive root

        Yields:
            Instances of the specified model class

        Note:
            Files that fail to parse as valid models are skipped with a warning.
        """
        import logging

        logger = logging.getLogger(__name__)

        dir_path = self._path_for(None, dir)
        if not dir_path.is_dir():
            return

        for name in self.list(dir or ""):
            path = dir_path / name
            if path.is_file():
                try:
                    yield self.read_model(cls, name, dir)
                except Exception as e:
                    logger.warning(f"Failed to read model from {path}: {e}")
