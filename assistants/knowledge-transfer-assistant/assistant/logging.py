"""
Logging utilities for knowledge transfer assistant.

This module provides enhanced logging capabilities for the knowledge transfer assistant,
including JSON formatting and file logging.
"""

import json
import logging
import os
import platform
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel

# Configure the root logger
logger = logging.getLogger("knowledge-transfer-assistant")
logger.setLevel(logging.DEBUG)

# Ensure propagation is enabled to allow logs to reach the root handler
logger.propagate = True

# Remove any existing handlers to avoid duplicates
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Add a null handler by default (to prevent "No handler found" warnings)
logger.addHandler(logging.NullHandler())

# Set up console handler with a specific format
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - [%(levelname)s] %(message)s")
console.setFormatter(formatter)
logger.addHandler(console)


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
    """Custom JSON encoder that handles UUIDs and datetimes."""

    def default(self, o: Any) -> Any:
        if isinstance(o, UUID):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


class JsonFormatter(logging.Formatter):
    """Formats log records as JSON objects."""

    def format(self, record) -> str:
        record_dict = record.__dict__
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "conversation_id": record_dict.get("conversation_id", None),
            "share_id": record_dict.get("share_id", None),
            "message": record.getMessage(),
            "data": record_dict.get("data", None),
            "module": record.module,
            "functionName": record.funcName,
            "lineNumber": record.lineno,
            "logger": record.name,
        }

        # Add any extra fields
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
                "conversation_id",
                "share_id",
                "data",
            ]
        }
        log_record.update(extra_fields)

        try:
            return json.dumps(log_record, cls=CustomEncoder)
        except Exception as e:
            # Fallback if serialization fails
            simple_record = {
                "timestamp": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "conversation_id": record_dict.get("conversation_id", None),
                "message": f"Error serializing log: {e}. Original message: {record.getMessage()}",
                "module": record.module,
                "lineNumber": record.lineno,
            }
            return json.dumps(simple_record)


def setup_file_logging(log_dir: Optional[str] = None) -> Path:
    """
    Set up file logging with JSON formatting.

    Args:
        log_dir: Directory for log files. If None, uses the knowledge transfer's .data/logs/ directory

    Returns:
        Path to the log file
    """
    if log_dir is None:
        current_file = Path(__file__)
        share_dir = current_file.parent.parent
        log_path = share_dir / ".data" / "logs"
    else:
        log_path = Path(log_dir)

    # Ensure directory exists
    log_path.mkdir(parents=True, exist_ok=True)

    # Create log file path with timestamp to avoid conflicts
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_path / f"log_{timestamp}.json"
    line_log_file = log_path / f"log_{timestamp}.log"  # Add a regular log file too

    try:
        # Remove any existing file handlers to avoid duplicates
        for handler in logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                logger.removeHandler(handler)

        # Set up JSON file handler
        json_file_handler = logging.FileHandler(log_file)
        json_file_handler.setLevel(logging.DEBUG)
        json_file_handler.setFormatter(JsonFormatter())
        logger.addHandler(json_file_handler)

        # Also set up a regular text file handler for easier debugging
        text_file_handler = logging.FileHandler(line_log_file)
        text_file_handler.setLevel(logging.DEBUG)
        text_file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - [%(levelname)s] %(message)s"))
        logger.addHandler(text_file_handler)

        logger.debug(
            f"File logging enabled: {log_file}",
            extra={
                "system": platform.system(),
                "python_version": platform.python_version(),
                "app": "knowledge-transfer-assistant",
                "path": str(log_file.absolute()),
            },
        )

        # Also force a flush to ensure the log is written immediately
        for handler in logger.handlers:
            if hasattr(handler, "flush"):
                handler.flush()

        # Set permissions to ensure files are readable (for debugging)
        try:
            import stat

            os.chmod(log_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
            os.chmod(line_log_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        except Exception as e:
            logger.warning(f"Could not set log file permissions: {e}")
            print(f"Permission error: {e}")

        print(f"Logging to files: {log_file} and {line_log_file}")

    except Exception as e:
        print(f"Failed to set up file logging: {e}")
        # Fall back to a different location in the .data directory
        try:
            # Try a different subfolder in the .data directory
            current_file = Path(__file__)
            share_dir = current_file.parent.parent
            fallback_dir = share_dir / ".data" / "fallback_logs"
            os.makedirs(fallback_dir, exist_ok=True)
            log_file = Path(fallback_dir) / f"log_{timestamp}.json"
            line_log_file = Path(fallback_dir) / f"log_{timestamp}.log"

            json_file_handler = logging.FileHandler(log_file)
            json_file_handler.setLevel(logging.DEBUG)
            json_file_handler.setFormatter(JsonFormatter())
            logger.addHandler(json_file_handler)

            text_file_handler = logging.FileHandler(line_log_file)
            text_file_handler.setLevel(logging.DEBUG)
            text_file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - [%(levelname)s] %(message)s"))
            logger.addHandler(text_file_handler)

            logger.warning(f"Using fallback log location: {log_file}")
            print(f"Fallback logging to: {log_file} and {line_log_file}")

        except Exception as fallback_error:
            print(f"Failed to set up fallback logging: {fallback_error}")

    return log_file


def extra_data(data: Any) -> Dict[str, Any]:
    """
    Helper function to prepare extra data for log messages.

    Args:
        data: Data to include in log entry

    Returns:
        Dictionary with 'data' key containing serialized data
    """
    extra = {}

    # Convert to serializable format
    data = convert_to_serializable(data)

    # Ensure data is JSON-serializable
    try:
        data = json.loads(json.dumps(data, cls=CustomEncoder))
    except Exception as e:
        data = str(e)

    if data:
        extra["data"] = data

    return extra


# Make extra_data available for import
__all__ = ["setup_file_logging", "extra_data", "logger"]
