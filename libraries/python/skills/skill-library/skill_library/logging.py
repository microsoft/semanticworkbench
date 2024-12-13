import json
import logging
from datetime import datetime
from os import PathLike
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import BaseModel

logger = logging.getLogger("skill-library")
logger.addHandler(logging.NullHandler())
logger.setLevel(logging.DEBUG)


def convert_to_serializable(data: Any) -> Any:
    """
    Recursively convert Pydantic BaseModel instances to dictionaries.
    """
    if isinstance(data, BaseModel):
        return data.model_dump()
    elif isinstance(data, dict):
        return {key: convert_to_serializable(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_to_serializable(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(convert_to_serializable(item) for item in data)
    elif isinstance(data, set):
        return {convert_to_serializable(item) for item in data}
    return data


class CustomEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, UUID):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


def extra_data(data: Any) -> dict[str, Any]:
    """
    Helper function to use when adding extra data to log messages.
    """
    extra = {}

    # Convert to serializable.
    data = convert_to_serializable(data)

    # Ensure data is a JSON-serializable object.
    try:
        data = json.loads(json.dumps(data, cls=CustomEncoder))
    except Exception as e:
        data = str(e)

    if data:
        extra["data"] = data

    return extra


extra_data = extra_data


class JsonFormatter(logging.Formatter):
    def format(self, record) -> str:
        record_dict = record.__dict__
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "sessionId": record_dict.get("session_id", None),
            "runIdd": record_dict.get("run_id", None),
            "message": record.getMessage(),
            "data": record_dict.get("data", None),
            "module": record.module,
            "functionName": record.funcName,
            "lineNumber": record.lineno,
            "logger": record.name,
        }
        extra_fields = {
            key: value
            for key, value in record.__dict__.items()
            if key
            not in [
                "levelname",
                "msg",
                "args",
                "funcName",
                "module",
                "lineno",
                "name",
                "message",
                "asctime",
                "session_id",
                "run_id",
                "data",
            ]
        }
        log_record.update(extra_fields)
        return json.dumps(log_record)


def file_logging_handler(logfile_path: PathLike, ensure_dir_exists: bool = False) -> logging.FileHandler:
    # Create the data directory if it does not exist.
    data_dir = Path(logfile_path).parent
    if ensure_dir_exists:
        if not data_dir.exists():
            data_dir.mkdir()
    else:
        if not data_dir.exists():
            raise FileNotFoundError(f"Logging directory {data_dir} does not exist.")

    file_handler = logging.FileHandler(Path(logfile_path))
    file_handler.setFormatter(JsonFormatter())
    return file_handler
