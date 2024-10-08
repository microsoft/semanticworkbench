import json
import logging
import os
import pathlib
from contextlib import contextmanager
from datetime import datetime
from shutil import rmtree
from typing import BinaryIO, Iterator

import magic
from context import Context
from pydantic import BaseModel, Field

# from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class DriveConfig(BaseModel):
    root: str = Field(default=".data/drive")
    context: Context | None = Field(default=None)

    class Config:
        arbitrary_types_allowed = True


class FileMetadata:
    dir: str | None
    filename: str
    content_type: str
    size: int
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    def __init__(self, filename: str, dir: str | None, content_type: str, size: int) -> None:
        self.filename = filename
        self.dir = dir
        self.content_type = content_type
        self.size = size

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "dir": self.dir,
            "content_type": self.content_type,
            "size": self.size,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __str__(self) -> str:
        if self.dir is None:
            path = self.filename
        else:
            path = f"{self.dir}/{self.filename}"
        return f"{path}\t{self.content_type}\t{self.size} bytes\t{self.created_at}\t{self.updated_at}"

    @staticmethod
    def from_bytes(content: BinaryIO, filename: str, dir: str | None = None) -> "FileMetadata":
        mime = magic.Magic(mime=True)
        content_type = mime.from_buffer(content.read())
        content.seek(0)
        size = len(content.read())
        return FileMetadata(filename=filename, dir=dir, content_type=content_type, size=size)


class File:
    metadata: FileMetadata
    content: BinaryIO

    def __init__(self, metadata: FileMetadata, content: BinaryIO) -> None:
        self.id = id
        self.metadata = metadata
        self.content = content

    @staticmethod
    def from_bytes(content: BinaryIO, filename: str, dir: str | None) -> "File":
        metadata = FileMetadata.from_bytes(content, filename, dir)
        return File(content=content, metadata=metadata)


class Drive:
    def __init__(self, settings: DriveConfig) -> None:
        self.context = settings.context if settings.context is not None else Context()
        self.root_path = pathlib.Path(settings.root) / self.context.session_id
        self.metadata_path = self.root_path / ".metadata"
        if not self.metadata_path.exists():
            self.metadata_path.mkdir(parents=True)

    def _path_for(self, filename: str | None = None, dir: str | None = None) -> pathlib.Path:
        """Return the actual path for a dir/file combo, creating the dir as needed."""
        namespace_path = self.root_path / (dir or "")
        namespace_path.mkdir(parents=True, exist_ok=True)
        if filename is None:
            return namespace_path
        return namespace_path / filename

    def _metadata_path_for(self, filename: str | None = None, dir: str | None = None) -> pathlib.Path:
        """Return the actual path for a dir/file combo, creating the dir as needed."""
        namespace_path = self.metadata_path / (dir or "")
        namespace_path.mkdir(parents=True, exist_ok=True)
        if filename is None:
            return namespace_path
        return namespace_path / (filename + ".json")

    def _unique_filename(self, filename: str, dir: str | None) -> str:
        """Ensure filename is unique in the namespace by appending a counter."""
        root_name, extension = os.path.splitext(filename)
        counter = 1
        while self.file_exists(dir, filename):
            filename = f"{root_name}({counter}){extension}"
            counter += 1

        return filename

    def add_bytes(
        self,
        content: BinaryIO,
        filename: str,
        dir: str | None = None,
        overwrite: bool = False,
    ) -> FileMetadata:
        # If file exists, and asked to overwrite, use the same file id.
        # If not asked to overwrite, generate a new file id and modified filename.
        if self.file_exists(dir, filename):
            if not overwrite:
                filename = self._unique_filename(filename, dir)

        file = File.from_bytes(content, filename, dir)

        # Write file.
        file_path = self._path_for(file.metadata.filename, file.metadata.dir)
        with open(file_path, "wb") as f:
            content.seek(0)
            f.write(content.read())

        # Write metadata.
        metadata_path = self._metadata_path_for(file.metadata.filename, file.metadata.dir)
        with open(metadata_path, "w") as f:
            f.write(json.dumps(file.metadata.to_dict(), indent=2))

        return file.metadata

    def delete(self, dir: str | None = None, filename: str | None = None) -> None:
        file_path = self._path_for(dir, filename)
        if file_path.is_file():
            file_path.unlink()
            metadata_path = self._metadata_path_for(dir)
            metadata_path.unlink()
        else:
            dir_path = self._path_for(dir)
            if dir_path.is_dir():
                rmtree(dir_path)
            metadata_path = self._metadata_path_for(dir)
            if metadata_path.is_dir():
                rmtree(metadata_path)

    def read_all_files(self, dir: str) -> Iterator[BinaryIO]:
        dir_path = self._path_for(dir, "")
        if not dir_path.is_dir():
            return

        for file_path in dir_path.iterdir():
            with open(file_path, "rb") as f:
                yield f

    def list(self, dir: str = "") -> Iterator[str]:
        dir_path = self._path_for(dir, "")
        if not dir_path.is_dir():
            return

        for file_path in dir_path.iterdir():
            # Don't include .metadata
            if file_path.name == ".metadata":
                continue
            yield file_path.name

    @contextmanager
    def read_file(self, dir: str, filename: str) -> Iterator[BinaryIO]:
        file_path = self._path_for(dir, filename)
        with open(file_path, "rb") as f:
            yield f

    def file_exists(self, dir: str | None, filename: str) -> bool:
        file_path = self._path_for(filename, dir)
        return file_path.exists()
