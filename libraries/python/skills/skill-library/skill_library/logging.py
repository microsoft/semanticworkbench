import json
import logging
from os import PathLike
from pathlib import Path
from typing import Any

logger = logging.getLogger("skill_library")
logger.addHandler(logging.NullHandler())


def add_serializable_data(data: Any) -> dict[str, Any]:
    """
    Helper function to use when adding extra data to log messages.
    """
    extra = {}

    # Ensure data is a JSON-serializable object.
    try:
        data = json.loads(json.dumps(data))
    except Exception as e:
        data = str(e)

    if data:
        extra["data"] = data

    return extra


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
