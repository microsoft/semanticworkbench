from ._inspector import WhiteboardInspector
from ._whiteboard import get_whiteboard_service_config, notify_whiteboard

__all__ = [
    "notify_whiteboard",
    "WhiteboardInspector",
    "get_whiteboard_service_config",
]
