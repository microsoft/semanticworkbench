import uuid
from enum import Enum

from pydantic import BaseModel, Field


class ToDoItemStatus(Enum):
    """
    Enum for the status of a to-do item.
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ToDoItemPriority(Enum):
    """
    Enum for the priority of a to-do item.
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ToDoItem(BaseModel):
    """
    A class to represent a single to-do item.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # Unique identifier
    content: str
    priority: str = "medium"  # Default priority is 'medium'
    status: str = "pending"  # Default status is 'pending'


class ToDoList(BaseModel):
    """
    A class to represent a to-do list.
    """

    items: list[ToDoItem] = Field(default_factory=list)

    def add(self, todo: ToDoItem) -> None:
        """
        Add a new to-do item.
        """
        self.items.append(todo)

    def remove(self, id: str) -> None:
        """
        Remove a to-do item.
        """
        self.items = [item for item in self.items if item.id != id]

    def list(self) -> list[ToDoItem]:
        """
        List all to-do items.
        """
        return self.items
