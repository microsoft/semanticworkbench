from typing import Any, Awaitable, Callable

from mcp import ServerNotification
from mcp.types import CallToolResult
from pydantic import BaseModel

ToolCallFunction = Callable[[], Awaitable[CallToolResult]]
ServerNotificationHandler = Callable[[ServerNotification], Awaitable[None]]


class ToolCallProgressMessage(BaseModel):
    """
    Represents a progress message for an active tool call.

    Attributes:
        message (str): A brief textual update describing the current tool execution state.
        data (dict[str, Any] | None): Optional dictionary containing structured data relevant
            to the progress update.
    """

    message: str
    data: dict[str, Any] | None
