"""
Chat drivers integrate with other systems primarily by emitting events. The
driver consumer is responsible for handling all events emitted by the driver.

When integrating a driver with the the Semantic Workbench, you may find it
helpful to handle all Information, or Error, or Status events in particular
Semantic Workbench ways by default. For that reason, the driver should generally
prefer to emit events (from its functions) that inherit from one of these
events.
"""

from datetime import datetime
from typing import Any, Callable, Optional, Protocol, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EventProtocol(Protocol):
    id: UUID
    session_id: Optional[str]
    timestamp: datetime
    message: Optional[str]
    metadata: dict[str, Any]
    to_json: Callable[[], str]


TEvent = TypeVar("TEvent", covariant=True, bound=EventProtocol)


class BaseEvent(BaseModel):
    """
    All events inherit from the `BaseEvent` class. The `BaseEvent` class defines
    the common fields that, by convention,  all events must have.
    """

    id: UUID = Field(default_factory=uuid4)
    session_id: str | None = Field(default=None)
    timestamp: datetime = Field(default_factory=datetime.now)
    message: str | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.message}"

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)


class InformationEvent(BaseEvent):
    pass


class ErrorEvent(BaseEvent):
    pass


class StatusUpdatedEvent(BaseEvent):
    pass


class MessageEvent(BaseEvent):
    pass


class NoticeEvent(BaseEvent):
    pass
