import inspect
import json
from typing import Any

from openai import (
    NotGiven,
)
from pydantic import BaseModel


def make_completion_args_serializable(completion_args: dict[str, Any]) -> dict[str, Any]:
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
