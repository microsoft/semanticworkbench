"""
Data models for mission entities (briefings, field requests, logs, etc.)

This module provides the core data structures for the mission assistant, 
without any artifact abstraction or unnecessary complexity.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MissionState(str, Enum):
    """States for mission progression."""
    
    PLANNING = "planning"
    READY_FOR_FIELD = "ready_for_field"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABORTED = "aborted"


class RequestPriority(str, Enum):
    """Priority levels for field requests."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RequestStatus(str, Enum):
    """Status options for field requests."""

    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DEFERRED = "deferred"
    CANCELLED = "cancelled"


class LogEntryType(str, Enum):
    """Types of log entries in the mission log."""

    BRIEFING_CREATED = "briefing_created"
    BRIEFING_UPDATED = "briefing_updated"
    REQUEST_CREATED = "request_created"
    REQUEST_UPDATED = "request_updated"
    REQUEST_RESOLVED = "request_resolved"
    STATUS_CHANGED = "status_changed"
    GOAL_COMPLETED = "goal_completed"
    CRITERION_COMPLETED = "criterion_completed"
    PARTICIPANT_JOINED = "participant_joined"
    PARTICIPANT_LEFT = "participant_left"
    MISSION_STARTED = "mission_started"
    MISSION_COMPLETED = "mission_completed"
    MISSION_ABORTED = "mission_aborted"
    GATE_PASSED = "gate_passed"
    INFORMATION_UPDATE = "information_update"
    FILE_SHARED = "file_shared"
    KB_UPDATE = "kb_update"
    CUSTOM = "custom"


class BaseEntity(BaseModel):
    """Base class for all mission entities."""

    version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str  # User ID
    updated_by: str  # User ID
    conversation_id: str  # Source conversation ID


class SuccessCriterion(BaseModel):
    """A specific measurable criterion that defines mission success."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    completed: bool = False
    completed_at: Optional[datetime] = None
    completed_by: Optional[str] = None  # User ID who completed the criterion


class MissionGoal(BaseModel):
    """A specific goal for the mission with associated success criteria."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    priority: int = 1  # 1 = highest, increasing numbers = lower priority
    success_criteria: List[SuccessCriterion] = Field(default_factory=list)


class MissionBriefing(BaseEntity):
    """
    A clear, concise statement of the mission, including goals,
    success criteria, and high-level context.
    """

    mission_name: str
    mission_description: str
    goals: List[MissionGoal] = Field(default_factory=list)
    timeline: Optional[str] = None
    additional_context: Optional[str] = None


class KBSection(BaseModel):
    """A section of the mission knowledge base with specific content."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    order: int
    tags: List[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    updated_by: str  # User ID


class MissionKB(BaseEntity):
    """
    The curated information necessary for the Field to carry out
    the mission, kept up-to-date by HQ.
    """

    sections: Dict[str, KBSection] = Field(default_factory=dict)  # section_id -> KBSection


class MissionStatus(BaseEntity):
    """
    A dynamic representation of progress toward success,
    updated in real time to reflect remaining tasks and progress.
    """

    # State of the mission
    state: MissionState = MissionState.PLANNING

    # Overall progress percentage (0-100)
    progress_percentage: int = 0

    # Copy of all goals with their current status
    goals: List[MissionGoal] = Field(default_factory=list)

    # Active request IDs that are currently blocking progress
    active_blockers: List[str] = Field(default_factory=list)

    # Number of completed success criteria out of total
    completed_criteria: int = 0
    total_criteria: int = 0

    # Custom status message
    status_message: Optional[str] = None

    # Next actions or upcoming milestones
    next_actions: List[str] = Field(default_factory=list)

    # Lifecycle metadata for tracking mission gates
    lifecycle: Dict[str, Any] = Field(default_factory=dict)


class FieldRequest(BaseEntity):
    """
    A specific information need or blocker submitted by field personnel
    that requires HQ support to resolve.
    """

    # Request identification
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Request details
    title: str
    description: str
    priority: RequestPriority = RequestPriority.MEDIUM
    status: RequestStatus = RequestStatus.NEW

    # Reference to the related goal(s) if applicable
    related_goal_ids: List[str] = Field(default_factory=list)

    # Resolution information
    resolution: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None  # User ID

    # Updates and comments on this request
    updates: List[Dict[str, Any]] = Field(default_factory=list)


class LogEntry(BaseModel):
    """Individual entry in the mission log."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    entry_type: LogEntryType
    message: str
    user_id: str
    user_name: str

    # Optional additional context for the entry
    related_entity_id: Optional[str] = None  # ID of related entity (e.g. field request ID)
    entity_type: Optional[str] = None  # Type of related entity
    metadata: Optional[Dict] = None


class MissionLog(BaseEntity):
    """
    A chronological record of all actions and interactions during the mission,
    including updates and progress reports.
    """

    entries: List[LogEntry] = Field(default_factory=list)