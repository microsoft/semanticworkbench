"""
Data models for mission artifacts shared between conversations.

These models define the structure for the five key artifacts:
1. Mission Briefing: A clear statement of mission goals and success criteria
2. Mission KB: Knowledge base with information needed for the mission
3. Mission Status: Real-time representation of mission progress
4. Field Requests: List of information needs and blockers from field personnel
5. Mission Log: Chronological record of all actions and interactions
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel, Field, model_validator


class ArtifactType(str, Enum):
    """Types of artifacts that can be shared between conversations."""

    MISSION_BRIEFING = "mission_briefing"
    MISSION_KB = "mission_kb"
    MISSION_STATUS = "mission_status"
    FIELD_REQUEST = "field_request"
    MISSION_LOG = "mission_log"


class BaseArtifact(BaseModel):
    """Base class for all mission artifacts."""

    artifact_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    artifact_type: ArtifactType
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
    completed_by: Optional[str] = None  # User ID


class MissionGoal(BaseModel):
    """A specific goal for the mission with associated success criteria."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    priority: int = 1  # 1 = highest, increasing numbers = lower priority
    success_criteria: List[SuccessCriterion] = Field(default_factory=list)


class MissionBriefing(BaseArtifact):
    """
    A clear, concise statement of the mission, including goals,
    success criteria, and high-level context.
    """

    artifact_type: ArtifactType = ArtifactType.MISSION_BRIEFING
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


class MissionKB(BaseArtifact):
    """
    The curated information necessary for the Field to carry out
    the mission, kept up-to-date by HQ.
    """

    artifact_type: ArtifactType = ArtifactType.MISSION_KB
    sections: Dict[str, KBSection] = Field(default_factory=dict)  # section_id -> KBSection

    @model_validator(mode="after")
    def validate_sections(self):
        """Ensure section IDs match the keys in the dictionary."""
        for section_id, section in self.sections.items():
            if section_id != section.id:
                raise ValueError(f"Section ID mismatch: key {section_id} != section.id {section.id}")
        return self


class MissionStatus(BaseArtifact):
    """
    A dynamic representation of progress toward success,
    updated in real time to reflect remaining tasks and progress.
    """

    artifact_type: ArtifactType = ArtifactType.MISSION_STATUS

    # Status can be one of: planning, in_progress, blocked, completed, aborted
    status: str = "planning"

    # Overall progress percentage (0-100)
    progress: int = 0

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


class FieldRequest(BaseArtifact):
    """
    A specific information need or blocker submitted by field personnel
    that requires HQ support to resolve.
    """

    artifact_type: ArtifactType = ArtifactType.FIELD_REQUEST

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
    updates: List[Dict[str, Union[str, datetime]]] = Field(default_factory=list)


class LogEntryType(str, Enum):
    """Types of log entries in the mission log."""

    ARTIFACT_CREATED = "artifact_created"
    ARTIFACT_UPDATED = "artifact_updated"
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
    CUSTOM = "custom"


class LogEntry(BaseModel):
    """Individual entry in the mission log."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    entry_type: LogEntryType
    message: str
    user_id: str
    user_name: str

    # Optional additional context for the entry
    artifact_id: Optional[str] = None
    artifact_type: Optional[ArtifactType] = None
    metadata: Optional[Dict] = None


class MissionLog(BaseArtifact):
    """
    A chronological record of all actions and interactions during the mission,
    including updates to artifacts and progress reports.
    """

    artifact_type: ArtifactType = ArtifactType.MISSION_LOG
    entries: List[LogEntry] = Field(default_factory=list)


class ArtifactVersion(BaseModel):
    """Version information for tracking artifact updates."""

    artifact_id: str
    artifact_type: ArtifactType
    version: int
    timestamp: datetime
    updated_by: str  # User ID

    # Optional conflict information
    has_conflict: bool = False
    conflict_details: Optional[str] = None


class ArtifactMessage(BaseModel):
    """
    Message format for sending artifacts between conversations.
    This structure will be serialized and included in message metadata.
    """

    message_type: str = "artifact_update"  # Used to identify artifact messages
    artifact_type: ArtifactType
    artifact_data: Dict  # Serialized artifact
    version_info: ArtifactVersion
    source_conversation_id: str
    target_conversation_id: str
    sync_timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Flag to indicate if this is just a notification or contains full data
    is_notification_only: bool = False

    # For large artifacts, indicates if this is a partial update
    is_partial_update: bool = False
    chunk_info: Optional[Dict] = None  # Information about chunking for large artifacts


ArtifactTypes = Union[MissionBriefing, MissionKB, MissionStatus, FieldRequest, MissionLog]


def get_artifact_type(artifact_type: str) -> Type[ArtifactTypes]:
    """
    Helper function to get the artifact type based on the string value.
    """
    if artifact_type == ArtifactType.MISSION_BRIEFING:
        return MissionBriefing
    elif artifact_type == ArtifactType.MISSION_KB:
        return MissionKB
    elif artifact_type == ArtifactType.MISSION_STATUS:
        return MissionStatus
    elif artifact_type == ArtifactType.FIELD_REQUEST:
        return FieldRequest
    elif artifact_type == ArtifactType.MISSION_LOG:
        return MissionLog
    else:
        raise ValueError(f"Unknown artifact type: {artifact_type}")
