"""
Data models for project entities (briefs, information requests, logs, etc.)

This module provides the core data structures for the project assistant,
without any artifact abstraction or unnecessary complexity.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class KnowledgeTransferState(str, Enum):
    """
    States for knowledge transfer progression.

    The transfer state represents the current phase of the knowledge transfer lifecycle.
    Knowledge transfer follows a standard flow: ORGANIZING -> READY_FOR_TRANSFER -> ACTIVE_TRANSFER -> COMPLETED.
    ARCHIVED is a terminal state that can be reached from any other state if the knowledge package is archived.
    """

    ORGANIZING = "organizing"  # Initial state - Coordinator is capturing and organizing knowledge
    READY_FOR_TRANSFER = "ready_for_transfer"  # Knowledge is organized and ready for team members to access
    ACTIVE_TRANSFER = "active_transfer"  # Team members are actively learning and exploring the knowledge
    COMPLETED = "completed"  # Learning objectives have been achieved and the transfer is complete
    ARCHIVED = "archived"  # Knowledge package was archived or is no longer active


class RequestPriority(str, Enum):
    """
    Priority levels for information requests.

    Defines the urgency of a request from a team member to the Coordinator.
    Higher priority requests should be addressed more quickly by the Coordinator.
    MEDIUM is the default priority for most requests.
    """

    LOW = "low"  # Non-urgent request, can be addressed when convenient
    MEDIUM = "medium"  # Standard priority for most requests
    HIGH = "high"  # Urgent request requiring prompt attention
    CRITICAL = "critical"  # Highest priority, requires immediate attention from the Coordinator


class RequestStatus(str, Enum):
    """
    Status options for information requests.

    Represents the lifecycle of an information request from creation to resolution.
    Requests typically progress from NEW -> ACKNOWLEDGED -> IN_PROGRESS -> RESOLVED.
    DEFERRED indicates requests that will be addressed later.
    """

    NEW = "new"  # Request has been created but not yet acknowledged by the Coordinator
    ACKNOWLEDGED = "acknowledged"  # Coordinator has seen the request but hasn't started working on it
    IN_PROGRESS = "in_progress"  # Coordinator is actively working on the request
    RESOLVED = "resolved"  # Coordinator has provided a resolution to the request
    DEFERRED = "deferred"  # Request handling has been postponed to a later time


class LogEntryType(str, Enum):
    """
    Types of log entries in the project log.

    These entry types categorize all events that can occur during a project.
    Log entries provide a chronological history of actions and events in the project,
    allowing both Coordinators and team members to track progress and changes.
    """

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

    # Backward compatibility for old log entries
    KB_UPDATE = "kb_update"  # Legacy alias for KNOWLEDGE_DIGEST_UPDATE
    GOAL_ADDED = "goal_added"  # Legacy alias for LEARNING_OBJECTIVE_ADDED


class BaseEntity(BaseModel):
    """
    Base class for all project entities.

    Provides common fields and behavior that all project-related data models inherit.
    This ensures consistency in how entities are created, versioned, and tracked.
    All derived classes will have proper timestamps and creator information.
    """

    version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str  # User ID
    updated_by: str  # User ID
    conversation_id: str  # Source conversation ID


class LearningOutcome(BaseModel):
    """
    A specific measurable learning outcome that defines knowledge transfer success.

    Learning outcomes are individual checkpoints that must be achieved
    to accomplish a learning objective. Each outcome represents a concrete,
    verifiable understanding or skill that can be marked as achieved.

    When all learning outcomes for all objectives are achieved, the knowledge
    transfer can be considered successful. Team members typically report when
    outcomes have been achieved.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # Unique identifier for the outcome
    description: str  # Clear, specific description of what needs to be understood or accomplished
    achieved: bool = False  # Whether this outcome has been achieved
    achieved_at: Optional[datetime] = None  # When the outcome was marked as achieved
    achieved_by: Optional[str] = None  # User ID of the person who achieved the outcome


class LearningObjective(BaseModel):
    """
    A specific learning objective with associated learning outcomes.

    Learning objectives represent the major knowledge areas that need to be understood
    for the knowledge transfer to be successful. Each objective consists of a name, description,
    priority level, and a list of specific learning outcomes that define when
    the objective can be considered achieved.

    Objectives are typically set by the Coordinator during knowledge organization and then tracked
    by both the Coordinator and team members throughout the knowledge transfer.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # Unique identifier for the objective
    name: str  # Short, clear name of the learning objective
    description: str  # Detailed description of what should be learned
    priority: int = 1  # Priority level (1 = highest priority, increasing numbers = lower priority)
    learning_outcomes: List[LearningOutcome] = Field(default_factory=list)  # List of outcomes to achieve


class KnowledgeBrief(BaseEntity):
    """
    A thorough, comprehensive documentation of the knowledge to be transferred,
    containing all relevant information necessary for understanding and learning.

    The brief is the primary document that defines the knowledge package.
    It serves as the central reference for both the Coordinator and team members
    to understand what needs to be learned and why, capturing the comprehensive
    context of the knowledge being transferred.

    The brief includes learning objectives, outcomes, and complete context.
    It focuses on capturing comprehensive knowledge through detailed description
    and additional_context fields that help learners understand the scope and purpose.

    Created by the Coordinator during the ORGANIZING phase, the brief must be
    completed before the knowledge can move to the READY_FOR_TRANSFER state.
    Once team members begin learning, the brief can still be updated,
    but major changes should be communicated to all participants.
    """

    title: str  # Short, distinctive title for the knowledge package to transfer
    description: str  # Comprehensive description of the knowledge's purpose, scope, and context
    timeline: Optional[str] = None  # Expected timeline for learning (optional)
    additional_context: Optional[str] = None  # Detailed supplementary information for knowledge transfer participants


class KnowledgeDigest(BaseEntity):
    """
    A dynamic knowledge digest that gets automatically updated as the coordinator organizes knowledge.

    The knowledge digest captures and maintains important knowledge context that emerges during
    conversations. It is automatically updated after each assistant message by analyzing
    the conversation history and extracting key information in FAQ format.

    Unlike a traditional knowledge base with separate sections, the digest is a single
    consolidated view that shows the most relevant information for the knowledge transfer. It serves as
    a dynamic, evolving source of truth that all team members can reference.
    """

    content: str = ""  # Markdown content for the knowledge digest (FAQ format)
    is_auto_generated: bool = True  # Whether the content was auto-generated or manually edited


class InformationRequest(BaseEntity):
    """
    A specific information need or blocker submitted by team members
    that requires Coordinator support to resolve.

    Information requests are the primary communication mechanism for team members
    to request assistance, information, or resources from the Coordinator. They represent
    questions, blockers, or needs that arise during project execution.

    The lifecycle of an information request typically follows:
    1. Created by a team member (NEW status)
    2. Seen by the Coordinator (ACKNOWLEDGED status)
    3. Worked on by the Coordinator (IN_PROGRESS status)
    4. Completed with a resolution (RESOLVED status)

    Requests can also be DEFERRED for later handling or CANCELLED if no longer relevant.
    The request priority helps the Coordinator prioritize which requests to handle first.
    """

    # Request identification
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # Unique ID for this request

    # Request details
    title: str  # Short summary of the request
    description: str  # Detailed explanation of what is needed
    priority: RequestPriority = RequestPriority.MEDIUM  # Urgency level of the request
    status: RequestStatus = RequestStatus.NEW  # Current status in the request lifecycle

    # Reference to the related learning objective(s) if applicable
    related_objective_ids: List[str] = Field(default_factory=list)  # IDs of learning objectives this request relates to

    # Resolution information
    resolution: Optional[str] = None  # The answer or solution provided by the Coordinator
    resolved_at: Optional[datetime] = None  # When the request was resolved
    resolved_by: Optional[str] = None  # User ID of the Coordinator who resolved this request

    # Updates and comments on this request
    updates: List[Dict[str, Any]] = Field(default_factory=list)  # History of status updates and comments


class LogEntry(BaseModel):
    """
    Individual entry in the project log.

    Log entries record all significant events that occur during a project.
    Each entry has a specific type, message, and associated metadata.

    The chronological sequence of log entries forms a complete audit trail
    of the project's progress, actions taken, and events that occurred.
    This provides accountability and helps with post-project review.

    Log entries are typically created automatically by the system when
    certain actions are taken, but can also be manually added by participants.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # Unique identifier for this log entry
    timestamp: datetime = Field(default_factory=datetime.utcnow)  # When this entry was created
    entry_type: LogEntryType  # The category/type of this log entry
    message: str  # Human-readable description of what happened
    user_id: str  # ID of the user who performed the action or triggered the event
    user_name: str  # Name of the user, for display purposes

    # Optional additional context for the entry
    related_entity_id: Optional[str] = None  # ID of related entity (e.g., information request ID)
    entity_type: Optional[str] = None  # Type of related entity (e.g., "information_request", "learning_objective")
    metadata: Optional[Dict] = None  # Additional structured data about the event


class KnowledgePackageLog(BaseModel):
    """
    A chronological record of all actions and interactions during the project,
    including updates and progress reports.

    The project log serves as the comprehensive history of everything that
    happened during a project. It contains a chronological list of log entries
    describing actions, state changes, and significant events.

    The log is used for:
    - Real-time monitoring of project activity
    - Post-project review and analysis
    - Accountability and documentation purposes
    - Tracking the sequence of events leading to outcomes

    Both the Coordinator and team members can view the project log, providing transparency
    into what has occurred during the project.
    """

    entries: List[LogEntry] = Field(default_factory=list)  # Chronological list of log entries


class KnowledgePackageInfo(BaseModel):
    """
    Core information about a knowledge package.

    This model stores essential knowledge package metadata that doesn't fit into other
    specific models like brief or digest. It's the central reference point
    for knowledge package identification, state, and team collaboration settings.
    """

    share_id: str  # Unique identifier for the knowledge package
    coordinator_conversation_id: Optional[str] = None  # ID of the coordinator's conversation
    transfer_state: KnowledgeTransferState = (
        KnowledgeTransferState.ORGANIZING
    )  # Current knowledge transfer lifecycle state
    transfer_notes: Optional[str] = None  # Notes about the knowledge transfer progress
    team_conversation_id: Optional[str] = None  # ID of the team conversation
    share_url: Optional[str] = None  # Shareable URL for inviting team members
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = None  # User ID who last updated the package info
    completion_percentage: Optional[int] = None  # Current learning completion percentage (0-100)
    next_learning_actions: List[str] = Field(default_factory=list)  # List of next learning actions
    version: int = 1  # Version counter for tracking changes
    achieved_outcomes: int = 0  # Count of achieved learning outcomes
    total_outcomes: int = 0  # Total count of learning outcomes
    transfer_lifecycle: Dict[str, Any] = Field(default_factory=dict)  # Transfer lifecycle metadata


class KnowledgePackage(BaseModel):
    """
    A comprehensive representation of a knowledge package, including its brief, digest,
    information requests, logs, and other related entities.

    This model encapsulates all the components that make up a knowledge transfer package,
    providing a single point of access to all relevant information for Coordinators and Team members.
    It serves as the main interface for interacting with the knowledge transfer data.
    """

    info: Optional[KnowledgePackageInfo]
    brief: Optional[KnowledgeBrief]
    learning_objectives: List[LearningObjective] = Field(default_factory=list)
    requests: List[InformationRequest] = Field(default_factory=list)
    digest: Optional[KnowledgeDigest]
    log: Optional[KnowledgePackageLog] = Field(default_factory=lambda: KnowledgePackageLog())
