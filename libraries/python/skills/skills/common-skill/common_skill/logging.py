import json
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

logger = logging.getLogger("guided-conversation-skill")
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


def add_serializable_data(data: Any) -> dict[str, Any]:
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


extra_data = add_serializable_data
