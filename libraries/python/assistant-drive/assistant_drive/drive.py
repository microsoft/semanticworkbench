import hashlib
import json
import logging
import os
import pathlib
from contextlib import contextmanager
from datetime import datetime
from typing import BinaryIO, Iterator, TypeVar
from uuid import UUID, uuid4

import magic
from context import Context
from pydantic import BaseModel, Field

# from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class DriveConfig(BaseModel):
    root: str = Field(default=".data/drive")
    context: Context | None = Field(default=None)
    ensure_safe_filenames: bool = Field(default=True)

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

    @staticmethod
    def from_bytes(content: BinaryIO, filename: str | None = None, dir: str | None = None) -> "FileMetadata":
        # Create a hash of the content to use as the filename if none is provided.
        if filename is None:
            sha256_hash = hashlib.sha256()
            for chunk in iter(lambda: content.read(4096), b""):
                sha256_hash.update(chunk)
            filename = sha256_hash.hexdigest()
            content.seek(0)

        mime = magic.Magic(mime=True)
        content_type = mime.from_buffer(content.read())
        content.seek(0)
        size = len(content.read())

        return FileMetadata(filename=filename, dir=dir, content_type=content_type, size=size)


class File:
    id: UUID
    metadata: FileMetadata
    content: BinaryIO

    def __init__(self, id: UUID, metadata: FileMetadata, content: BinaryIO) -> None:
        self.id = id
        self.metadata = metadata
        self.content = content

    @staticmethod
    def from_bytes(content: BinaryIO, filename: str | None, dir: str | None) -> "File":
        metadata = FileMetadata.from_bytes(content, filename, dir)
        return File(id=uuid4(), content=content, metadata=metadata)


class Drive:
    def __init__(self, settings: DriveConfig) -> None:
        self.context = settings.context if settings.context is not None else Context()
        self.root_path = pathlib.Path(settings.root) / self.context.session_id
        self.metadata_path = self.root_path / ".metadata"
        if not self.metadata_path.exists():
            self.metadata_path.mkdir(parents=True)
        self._ensure_safe_filenames = settings.ensure_safe_filenames

    def _path_for(self, filename: str, dir: str | None = None) -> pathlib.Path:
        namespace_path = self.root_path / (dir or "")
        namespace_path.mkdir(parents=True, exist_ok=True)
        if not filename:
            return namespace_path

        return namespace_path / filename

    def add_bytes(
        self,
        content: BinaryIO,
        filename: str | None = None,
        dir: str | None = None,
    ) -> UUID:
        file = File.from_bytes(content, filename=filename, dir=dir)

        # Write file.
        file_path = self._path_for(str(file.id), file.metadata.dir)
        with open(file_path, "wb") as f:
            content.seek(0)
            f.write(content.read())

        # Write metadata.
        metadata_path = self.metadata_path / f"{file.id}.json"
        with open(metadata_path, "w") as f:
            f.write(json.dumps(file.metadata.to_dict(), indent=2))

        return file.id

    def delete_file(self, dir: str, filename: str) -> None:
        file_path = self._path_for(dir, filename)
        file_path.unlink(missing_ok=True)

    def read_all_files(self, dir: str) -> Iterator[BinaryIO]:
        dir_path = self._path_for(dir, "")
        if not dir_path.is_dir():
            return

        for file_path in dir_path.iterdir():
            with open(file_path, "rb") as f:
                yield f

    def list_files(self, dir: str = "") -> Iterator[str]:
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

    def file_exists(self, dir: str, filename: str) -> bool:
        file_path = self._path_for(dir, filename)
        return file_path.exists()


ModelT = TypeVar("ModelT", bound=BaseModel)


def model_write(file_path: os.PathLike, value: BaseModel) -> None:
    path = pathlib.Path(file_path)
    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    data_json = value.model_dump_json()
    path.write_text(data_json, encoding="utf-8")


ModelT = TypeVar("ModelT", bound=BaseModel)


def model_read(file_path: os.PathLike | str, cls: type[ModelT], strict: bool | None = None) -> ModelT | None:
    path = pathlib.Path(file_path)
    try:
        data_json = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None

    value = cls.model_validate_json(data_json, strict=strict)
    return value


def model_delete(file_path: os.PathLike) -> None:
    path = pathlib.Path(file_path)
    path.unlink(missing_ok=True)


def model_exists(file_path: os.PathLike) -> bool:
    path = pathlib.Path(file_path)
    return path.exists()


def model_list_files(dir_path: os.PathLike) -> Iterator[str]:
    path = pathlib.Path(dir_path)
    if not path.is_dir():
        return

    for file_path in path.iterdir():
        yield file_path.name


def model_read_all_files(dir_path: os.PathLike, cls: type[ModelT]) -> Iterator[ModelT]:
    path = pathlib.Path(dir_path)
    if not path.is_dir():
        return

    for file_path in path.iterdir():
        value = model_read(file_path, cls)
        if value is not None:
            yield value
