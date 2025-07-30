"""
Data models for knowledge transfer share entities (briefs, information requests, logs, etc.)

This module provides the core data structures for the knowledge transfer assistant,
without any artifact abstraction or unnecessary complexity.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ConversationRole(str, Enum):
    COORDINATOR = "coordinator"
    TEAM = "team"
    SHAREABLE_TEMPLATE = "shareable_template"


class ConversationShareInfo(BaseModel):
    share_id: str
    conversation_id: str
    role: ConversationRole


class InspectorTab(str, Enum):
    BRIEF = "brief"
    LEARNING = "learning"
    SHARING = "sharing"
    DEBUG = "debug"


class RequestPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RequestStatus(str, Enum):
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DEFERRED = "deferred"


class BaseEntity(BaseModel):
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    updated_by: str
    conversation_id: str


class LearningOutcomeAchievement(BaseModel):
    outcome_id: str
    achieved: bool = True
    achieved_at: datetime = Field(default_factory=datetime.utcnow)


class TeamConversationInfo(BaseModel):
    conversation_id: str
    redeemer_user_id: str
    redeemer_name: str
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    last_active_at: datetime = Field(default_factory=datetime.utcnow)
    outcome_achievements: list[LearningOutcomeAchievement] = Field(default_factory=list)


class LearningOutcome(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str


class LearningObjective(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    priority: int = 1
    learning_outcomes: list[LearningOutcome] = Field(default_factory=list)


class KnowledgeBrief(BaseEntity):
    title: str
    content: str
    timeline: str | None = None


class KnowledgeDigest(BaseEntity):
    content: str = ""
    is_auto_generated: bool = True


class InformationRequest(BaseEntity):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    priority: RequestPriority = RequestPriority.MEDIUM
    status: RequestStatus = RequestStatus.NEW
    related_objective_ids: list[str] = Field(default_factory=list)
    resolution: str | None = None
    resolved_at: datetime | None = None
    resolved_by: str | None = None

    # History of status updates and comments
    updates: list[dict[str, Any]] = Field(default_factory=list)


class LogEntryType(str, Enum):
    # Brief-related events
    BRIEFING_CREATED = "briefing_created"
    BRIEFING_UPDATED = "briefing_updated"

    # Learning Objective-related events
    LEARNING_OBJECTIVE_ADDED = "learning_objective_added"
    LEARNING_OBJECTIVE_DELETED = "learning_objective_deleted"
    LEARNING_OBJECTIVE_UPDATED = "learning_objective_updated"

    # Information request lifecycle events
    REQUEST_CREATED = "request_created"
    REQUEST_UPDATED = "request_updated"
    REQUEST_DELETED = "request_deleted"

    # Project state and progress events
    STATUS_CHANGED = "status_changed"
    OUTCOME_ATTAINED = "outcome_attained"
    REQUEST_RESOLVED = "request_resolved"
    LEARNING_OBJECTIVE_ACCOMPLISHED = "learning_objective_accomplished"

    # Participant events
    PARTICIPANT_JOINED = "participant_joined"
    PARTICIPANT_LEFT = "participant_left"

    # Share lifecycle events
    SHARE_STARTED = "share_started"
    SHARE_COMPLETED = "share_completed"
    SHARE_ABORTED = "share_aborted"

    # Miscellaneous events
    SHARE_INFORMATION_UPDATE = "share_information_update"
    FILE_SHARED = "file_shared"
    FILE_DELETED = "file_deleted"
    KNOWLEDGE_DIGEST_UPDATE = "knowledge_digest_update"
    CUSTOM = "custom"


class LogEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    entry_type: LogEntryType
    user_id: str
    user_name: str
    related_entity_id: str | None = None
    entity_type: str | None = None
    message: str
    metadata: dict | None = None


class KnowledgePackageLog(BaseModel):
    entries: list[LogEntry] = Field(default_factory=list)  # Chronological list of log entries


class KnowledgePackage(BaseModel):
    share_id: str
    coordinator_conversation_id: str | None = None
    shared_conversation_id: str | None = None
    team_conversations: dict[str, TeamConversationInfo] = Field(default_factory=dict)
    share_url: str | None = None

    version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: str | None = None

    # Package components
    audience: str | None = None
    brief: KnowledgeBrief | None
    learning_objectives: list[LearningObjective] = Field(default_factory=list)
    takeaways: list[str] = Field(default_factory=list)
    preferred_communication_style: str | None = None
    transfer_notes: str | None = None
    digest: KnowledgeDigest | None

    # Lifecycle
    is_intended_to_accomplish_outcomes: bool = True
    next_learning_actions: list[str] = Field(default_factory=list)
    transfer_lifecycle: dict[str, Any] = Field(default_factory=dict)
    knowledge_organized: bool = False
    archived: bool = False
    requests: list[InformationRequest] = Field(default_factory=list)

    log: KnowledgePackageLog | None = Field(default_factory=lambda: KnowledgePackageLog())


class CoordinatorConversationMessage(BaseModel):
    message_id: str
    content: str
    sender_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_assistant: bool = False


class CoordinatorConversationMessages(BaseModel):
    knowledge_share_id: str
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    messages: list[CoordinatorConversationMessage] = Field(default_factory=list)
