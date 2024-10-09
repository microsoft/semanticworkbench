import logging
import os
import pathlib
from typing import Any, Iterator, TypeVar

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class FileStorageSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="allow")

    root: str = ".data/files"


def write_model(file_path: os.PathLike, value: BaseModel, serialization_context: dict[str, Any] | None = None) -> None:
    """Write a pydantic model to a file."""
    path = pathlib.Path(file_path)
    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    data_json = value.model_dump_json(context=serialization_context)
    path.write_text(data_json, encoding="utf-8")


ModelT = TypeVar("ModelT", bound=BaseModel)


def read_model(file_path: os.PathLike | str, cls: type[ModelT], strict: bool | None = None) -> ModelT | None:
    """Read a pydantic model from a file."""
    path = pathlib.Path(file_path)

    try:
        data_json = path.read_text(encoding="utf-8")
    except (FileNotFoundError, ValueError):
        return None

    return cls.model_validate_json(data_json, strict=strict)


def read_models_in_dir(dir_path: os.PathLike, cls: type[ModelT]) -> Iterator[ModelT]:
    """Read pydantic models from all files in a directory."""
    path = pathlib.Path(dir_path)
    if not path.is_dir():
        return

    for file_path in path.iterdir():
        value = read_model(file_path, cls)
        if value is not None:
            yield value
