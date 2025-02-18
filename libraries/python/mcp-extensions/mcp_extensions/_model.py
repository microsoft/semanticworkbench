from typing import Any, Awaitable, Callable

from mcp import ServerNotification
from mcp.types import CallToolResult
from pydantic import BaseModel

ToolCallFunction = Callable[[], Awaitable[CallToolResult]]
ServerNotificationHandler = Callable[[ServerNotification], Awaitable[None]]


class ToolCallProgressMessage(BaseModel):
    message: str
    data: dict[str, Any] | None
