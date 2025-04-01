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
    """
    States for mission progression.

    The mission state represents the current phase of the mission lifecycle.
    Missions follow a standard flow: PLANNING -> READY_FOR_FIELD -> IN_PROGRESS -> COMPLETED.
    ABORTED is a terminal state that can be reached from any other state if the mission is canceled.
    """

    PLANNING = "planning"  # Initial state - HQ is defining the mission briefing and goals
    READY_FOR_FIELD = "ready_for_field"  # Mission is defined and ready for field agents to begin work
    IN_PROGRESS = "in_progress"  # Field agents are actively working on the mission
    COMPLETED = "completed"  # Mission goals have been achieved and the mission is complete
    ABORTED = "aborted"  # Mission was terminated early or canceled


class RequestPriority(str, Enum):
    """
    Priority levels for field requests.

    Defines the urgency of a request from a field agent to HQ.
    Higher priority requests should be addressed more quickly by HQ.
    MEDIUM is the default priority for most requests.
    """

    LOW = "low"  # Non-urgent request, can be addressed when convenient
    MEDIUM = "medium"  # Standard priority for most requests
    HIGH = "high"  # Urgent request requiring prompt attention
    CRITICAL = "critical"  # Highest priority, requires immediate attention from HQ


class RequestStatus(str, Enum):
    """
    Status options for field requests.

    Represents the lifecycle of a field request from creation to resolution.
    Requests typically progress from NEW -> ACKNOWLEDGED -> IN_PROGRESS -> RESOLVED.
    DEFERRED indicates requests that will be addressed later.
    CANCELLED is a terminal state for requests that are no longer relevant.
    """

    NEW = "new"  # Request has been created but not yet acknowledged by HQ
    ACKNOWLEDGED = "acknowledged"  # HQ has seen the request but hasn't started working on it
    IN_PROGRESS = "in_progress"  # HQ is actively working on the request
    RESOLVED = "resolved"  # HQ has provided a resolution to the request
    DEFERRED = "deferred"  # Request handling has been postponed to a later time
    CANCELLED = "cancelled"  # Request is no longer relevant or was canceled without resolution


class LogEntryType(str, Enum):
    """
    Types of log entries in the mission log.

    These entry types categorize all events that can occur during a mission.
    Log entries provide a chronological history of actions and events in the mission,
    allowing both HQ and field agents to track progress and changes.
    """

    # Briefing-related events
    BRIEFING_CREATED = "briefing_created"  # Initial creation of mission briefing
    BRIEFING_UPDATED = "briefing_updated"  # Any update to mission briefing content

    # Field request lifecycle events
    REQUEST_CREATED = "request_created"  # New field request submitted
    REQUEST_UPDATED = "request_updated"  # Status or content change in a request
    REQUEST_RESOLVED = "request_resolved"  # Field request marked as resolved

    # Mission state and progress events
    STATUS_CHANGED = "status_changed"  # Mission status or progress percentage updated
    GOAL_COMPLETED = "goal_completed"  # A mission goal marked as completed
    CRITERION_COMPLETED = "criterion_completed"  # Individual success criterion achieved

    # Participant events
    PARTICIPANT_JOINED = "participant_joined"  # New field agent joined the mission
    PARTICIPANT_LEFT = "participant_left"  # Participant left/disconnected from mission

    # Mission lifecycle events
    MISSION_STARTED = "mission_started"  # Mission transitioned to IN_PROGRESS state
    MISSION_COMPLETED = "mission_completed"  # Mission successfully completed
    MISSION_ABORTED = "mission_aborted"  # Mission terminated before completion

    # Miscellaneous events
    GATE_PASSED = "gate_passed"  # A milestone or checkpoint was passed
    INFORMATION_UPDATE = "information_update"  # General information or status update
    FILE_SHARED = "file_shared"  # A file was shared between participants
    KB_UPDATE = "kb_update"  # Knowledge base was updated
    CUSTOM = "custom"  # Custom log entry for specialized events


class BaseEntity(BaseModel):
    """
    Base class for all mission entities.

    Provides common fields and behavior that all mission-related data models inherit.
    This ensures consistency in how entities are created, versioned, and tracked.
    All derived classes will have proper timestamps and creator information.
    """

    version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str  # User ID
    updated_by: str  # User ID
    conversation_id: str  # Source conversation ID


class SuccessCriterion(BaseModel):
    """
    A specific measurable criterion that defines mission success.

    Success criteria are individual checkpoints that must be completed
    to achieve a mission goal. Each criterion represents a concrete,
    verifiable action or condition that can be marked as completed.

    When all success criteria for all goals are completed, the mission
    can be considered successful. Field agents typically report when
    criteria have been met.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # Unique identifier for the criterion
    description: str  # Clear, specific description of what needs to be accomplished
    completed: bool = False  # Whether this criterion has been met
    completed_at: Optional[datetime] = None  # When the criterion was marked as completed
    completed_by: Optional[str] = None  # User ID of the person who completed the criterion


class MissionGoal(BaseModel):
    """
    A specific goal for the mission with associated success criteria.

    Mission goals represent the major objectives that need to be accomplished
    for the mission to be successful. Each goal consists of a name, description,
    priority level, and a list of specific success criteria that define when
    the goal can be considered complete.

    Goals are typically set by HQ during mission planning and then tracked
    by both HQ and field agents throughout the mission.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # Unique identifier for the goal
    name: str  # Short, clear name of the goal
    description: str  # Detailed description of what the goal entails
    priority: int = 1  # Priority level (1 = highest priority, increasing numbers = lower priority)
    success_criteria: List[SuccessCriterion] = Field(default_factory=list)  # List of criteria to meet


class MissionBriefing(BaseEntity):
    """
    A clear, concise statement of the mission, including goals,
    success criteria, and high-level context.

    The mission briefing is the primary document that defines the mission.
    It serves as the central reference for both HQ and field agents
    to understand what needs to be accomplished and why.

    Created by HQ during the PLANNING phase, the briefing must be
    completed before the mission can move to the READY_FOR_FIELD state.
    Once field operations begin, the briefing can still be updated,
    but major changes should be communicated to all participants.
    """

    mission_name: str  # Short, distinctive name for the mission
    mission_description: str  # Comprehensive description of the mission's purpose and scope
    goals: List[MissionGoal] = Field(default_factory=list)  # List of mission goals
    timeline: Optional[str] = None  # Expected timeline or deadline information (free-form text)
    additional_context: Optional[str] = None  # Any other relevant information for mission participants


class KBSection(BaseModel):
    """
    A section of the mission knowledge base with specific content.

    Knowledge base sections allow HQ to organize and share important
    information with field agents. Each section focuses on a specific
    topic or area relevant to the mission.

    Sections can be added, updated, or removed as the mission progresses,
    allowing the knowledge base to evolve as new information becomes available.
    Tags help with categorization and searching within larger knowledge bases.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # Unique identifier for the section
    title: str  # Section title
    content: str  # Markdown content of the section
    order: int  # Display order within the KB (lower numbers appear first)
    tags: List[str] = Field(default_factory=list)  # Categorization tags for searching and filtering
    last_updated: datetime = Field(default_factory=datetime.utcnow)  # When the section was last modified
    updated_by: str  # User ID of the person who last updated this section


class MissionKB(BaseEntity):
    """
    The curated information necessary for the Field to carry out
    the mission, kept up-to-date by HQ.

    The mission knowledge base (KB) is a collection of organized information
    that field agents can reference while carrying out the mission. It complements
    the mission briefing by providing more detailed reference material.

    The KB is typically created by HQ during mission planning and can be
    continuously updated throughout the mission as new information becomes
    available or circumstances change. It serves as a single source of truth
    for mission-relevant information.
    """

    sections: Dict[str, KBSection] = Field(default_factory=dict)  # Dictionary mapping section_id to KBSection objects


class MissionStatus(BaseEntity):
    """
    A dynamic representation of progress toward success,
    updated in real time to reflect remaining tasks and progress.

    The mission status tracks the current state of the mission and its progress.
    It provides a snapshot of how far along the mission is toward completion
    and what state it's currently in (planning, in progress, etc.).

    Both HQ and field agents can update the mission status, typically with:
    - HQ updating the overall state (e.g., from PLANNING to READY_FOR_FIELD)
    - Field agents updating the progress percentage as they complete work

    The mission status is used by all mission participants to understand
    the current situation and what phase the mission is in.
    """

    # State of the mission
    state: MissionState = MissionState.PLANNING  # Current mission lifecycle state

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

    Field requests are the primary communication mechanism for field agents
    to request assistance, information, or resources from HQ. They represent
    questions, blockers, or needs that arise during field operations.

    The lifecycle of a field request typically follows:
    1. Created by a field agent (NEW status)
    2. Seen by HQ (ACKNOWLEDGED status)
    3. Worked on by HQ (IN_PROGRESS status)
    4. Completed with a resolution (RESOLVED status)

    Requests can also be DEFERRED for later handling or CANCELLED if no longer relevant.
    The request priority helps HQ prioritize which requests to handle first.
    """

    # Request identification
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # Unique ID for this request

    # Request details
    title: str  # Short summary of the request
    description: str  # Detailed explanation of what is needed
    priority: RequestPriority = RequestPriority.MEDIUM  # Urgency level of the request
    status: RequestStatus = RequestStatus.NEW  # Current status in the request lifecycle

    # Reference to the related goal(s) if applicable
    related_goal_ids: List[str] = Field(default_factory=list)  # IDs of mission goals this request relates to

    # Resolution information
    resolution: Optional[str] = None  # The answer or solution provided by HQ
    resolved_at: Optional[datetime] = None  # When the request was resolved
    resolved_by: Optional[str] = None  # User ID of the HQ member who resolved this request

    # Updates and comments on this request
    updates: List[Dict[str, Any]] = Field(default_factory=list)  # History of status updates and comments


class LogEntry(BaseModel):
    """
    Individual entry in the mission log.

    Log entries record all significant events that occur during a mission.
    Each entry has a specific type, message, and associated metadata.

    The chronological sequence of log entries forms a complete audit trail
    of the mission's progress, actions taken, and events that occurred.
    This provides accountability and helps with post-mission review.

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
    related_entity_id: Optional[str] = None  # ID of related entity (e.g., field request ID)
    entity_type: Optional[str] = None  # Type of related entity (e.g., "field_request", "goal")
    metadata: Optional[Dict] = None  # Additional structured data about the event


class MissionLog(BaseEntity):
    """
    A chronological record of all actions and interactions during the mission,
    including updates and progress reports.

    The mission log serves as the comprehensive history of everything that
    happened during a mission. It contains a chronological list of log entries
    describing actions, state changes, and significant events.

    The log is used for:
    - Real-time monitoring of mission activity
    - Post-mission review and analysis
    - Accountability and documentation purposes
    - Tracking the sequence of events leading to outcomes

    Both HQ and field agents can view the mission log, providing transparency
    into what has occurred during the mission.
    """

    entries: List[LogEntry] = Field(default_factory=list)  # Chronological list of log entries
