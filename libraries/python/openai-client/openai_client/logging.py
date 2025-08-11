import inspect
import json
from datetime import datetime
from typing import Any
from uuid import UUID

from openai import (
    NotGiven,
)
from pydantic import BaseModel


def make_completion_args_serializable(
    completion_args: dict[str, Any],
) -> dict[str, Any]:
    """
    We put the completion args into logs and messages, so it's important that
    they are serializable. This function returns a copy of the completion args
    that can be serialized.
    """
    sanitized = completion_args.copy()

    # NotGiven type (used by OpenAI) is not serializable.
    if isinstance(completion_args.get("tools"), NotGiven):
        del sanitized["tools"]

    # A pydantic BaseModel class is not serializable, and we don't want the
    # whole class anyway, so we just store the name.
    if completion_args.get("response_format"):
        response_format = completion_args["response_format"]
        if inspect.isclass(response_format) and issubclass(response_format, BaseModel):
            sanitized["response_format"] = response_format.__name__

    return sanitized


def convert_to_serializable(data: Any) -> Any:
    """
    Recursively convert Pydantic BaseModel instances to dictionaries.
    """
    if isinstance(data, BaseModel):
        return data.model_dump()
    elif inspect.isclass(data) and issubclass(data, BaseModel):
        # Handle Pydantic model classes (not instances)
        return data.__name__
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


def serializable(data: Any) -> dict[str, Any]:
    """
    Convert data to a serializable format for logging or other purposes.
    """
    data = convert_to_serializable(data)
    try:
        data = json.loads(json.dumps(data, cls=CustomEncoder))
    except Exception as e:
        data = str(e)
    return data


def add_serializable_data(data: Any) -> dict[str, Any]:
    """
    Helper function to use when adding extra data to log messages. Data will
    attempt to be put into a serializable format.
    """
    extra = {}
    data = serializable(data)
    if data:
        extra["data"] = data
    return extra


# Helpful alias
extra_data = add_serializable_data
