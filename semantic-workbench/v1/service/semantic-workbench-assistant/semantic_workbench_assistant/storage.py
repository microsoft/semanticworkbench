import hashlib
import io
import logging
import os
import pathlib
from contextlib import contextmanager
from typing import BinaryIO, Generic, Iterator, TypeVar

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class FileStorageSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="allow")

    root: str = ".data/files"
    ensure_safe_filenames: bool = True


class FileStorage:
    def __init__(self, settings: FileStorageSettings):
        self.root = pathlib.Path(settings.root)
        self._ensure_safe_filenames = settings.ensure_safe_filenames

    def _path_for(self, dir: str, filename: str, mkdir=False) -> pathlib.Path:
        namespace_path = self.root / dir
        if mkdir:
            namespace_path.mkdir(parents=True, exist_ok=True)

        if not filename:
            return namespace_path

        if not self._ensure_safe_filenames:
            return namespace_path / filename

        filename_hash = hashlib.sha256(filename.encode("utf-8")).hexdigest()
        return namespace_path / filename_hash

    def write_file(self, dir: str, filename: str, content: BinaryIO) -> None:
        file_path = self._path_for(dir, filename, mkdir=True)
        with open(file_path, "wb") as f:
            f.write(content.read())

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

    def list_files(self, dir: str) -> Iterator[str]:
        dir_path = self._path_for(dir, "")
        if not dir_path.is_dir():
            return

        for file_path in dir_path.iterdir():
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


class ModelStorage(Generic[ModelT]):
    """
    Provides file-system storage for pydantic models as a utility for assistant service
    implementations.
    """

    def __init__(self, cls: type[ModelT], file_storage: FileStorage, namespace: str) -> None:
        self._cls = cls
        self._file_storage = file_storage
        self._namespace = namespace

    def get_all(self) -> list[ModelT]:
        """
        Gets all the model values in the storage.
        """
        values = []
        try:
            for file in self._file_storage.read_all_files(dir=self._namespace):
                contents = file.read().decode("utf-8")
                value = self._cls.model_validate_json(contents)
                values.append(value)
        except FileNotFoundError:
            pass

        return values

    def get(self, key: str, strict: bool | None = None) -> ModelT | None:
        """
        Gets the model value for the given key, or None if the key does not exist. If the
        model has changed since the value was written, and is no longer valid, this will
        raise pydantic.ValidationError.
        """
        try:
            with self._file_storage.read_file(dir=self._namespace, filename=key) as file:
                contents = file.read().decode("utf-8")

        except FileNotFoundError:
            return None

        value = self._cls.model_validate_json(contents, strict=strict)
        return value

    def __getitem__(self, key: str) -> ModelT:
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value

    def set(self, key: str, value: ModelT) -> None:
        data_json = value.model_dump_json()
        self._file_storage.write_file(dir=self._namespace, filename=key, content=io.BytesIO(data_json.encode("utf-8")))

    def __setitem__(self, key: str, value: ModelT) -> None:
        self.set(key=key, value=value)

    def delete(self, key: str) -> None:
        self._file_storage.delete_file(dir=self._namespace, filename=key)
