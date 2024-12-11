import json
import logging
from typing import Any

logger = logging.getLogger(__name__)
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
