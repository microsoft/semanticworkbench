import hashlib
import logging
import pathlib
from contextlib import contextmanager
from typing import BinaryIO, Iterator

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class StorageSettings(BaseSettings):
    root: str = ".data/files"


class Storage:
    def __init__(self, settings: StorageSettings):
        self.root = pathlib.Path(settings.root)
        self._initialized = False

    def _ensure_initialized(self):
        if self._initialized:
            return
        self.root.mkdir(parents=True, exist_ok=True)
        self._initialized = True
        logger.info("initialized file storage; root: %s", self.root.absolute())

    def _file_path(self, namespace: str, filename: str, mkdir=False) -> pathlib.Path:
        self._ensure_initialized()
        namespace_path = self.root / namespace
        if mkdir:
            namespace_path.mkdir(exist_ok=True)
        filename_hash = hashlib.sha256(filename.encode("utf-8")).hexdigest()
        return namespace_path / filename_hash

    def file_exists(self, namespace: str, filename: str) -> bool:
        file_path = self._file_path(namespace, filename)
        return file_path.exists()

    def write_file(self, namespace: str, filename: str, content: BinaryIO) -> None:
        file_path = self._file_path(namespace, filename, mkdir=True)
        with open(file_path, "wb") as f:
            f.write(content.read())

    def delete_file(self, namespace: str, filename: str) -> None:
        file_path = self._file_path(namespace, filename)
        file_path.unlink(missing_ok=True)

    @contextmanager
    def read_file(self, namespace: str, filename: str) -> Iterator[BinaryIO]:
        file_path = self._file_path(namespace, filename)
        with open(file_path, "rb") as f:
            yield f
