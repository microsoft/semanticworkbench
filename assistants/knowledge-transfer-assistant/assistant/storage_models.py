"""
Models for project storage entities.

This module contains data models specific to storage operations,
separate from the core project data models.
"""

from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class ConversationRole(str, Enum):
    """
    Enumeration of conversation roles in a project.

    This enum represents the role that a conversation plays in a project,
    either as a Coordinator (managing the project) or as a Team member
    (participating in the project).
    """

    COORDINATOR = "coordinator"
    TEAM = "team"


class CoordinatorConversationMessage(BaseModel):
    """Model for storing a message from Coordinator conversation for Team access."""

    message_id: str
    content: str
    sender_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_assistant: bool = False


class CoordinatorConversationStorage(BaseModel):
    """Model for storing a collection of Coordinator conversation messages."""

    project_id: str
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    messages: List[CoordinatorConversationMessage] = Field(default_factory=list)