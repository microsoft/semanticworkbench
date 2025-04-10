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


class ProjectState(str, Enum):
    """
    States for project progression.

    The project state represents the current phase of the project lifecycle.
    Projects follow a standard flow: PLANNING -> READY_FOR_WORKING -> IN_PROGRESS -> COMPLETED.
    ABORTED is a terminal state that can be reached from any other state if the project is canceled.
    """

    PLANNING = "planning"  # Initial state - Coordinator is defining the project brief and goals
    READY_FOR_WORKING = "ready_for_working"  # Project is defined and ready for team members to begin work
    IN_PROGRESS = "in_progress"  # Team members are actively working on the project
    COMPLETED = "completed"  # Project goals have been achieved and the project is complete
    ABORTED = "aborted"  # Project was terminated early or canceled


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
    BRIEFING_CREATED = "briefing_created"  # Initial creation of project brief
    BRIEFING_UPDATED = "briefing_updated"  # Any update to project brief content

    # Information request deletion event
    REQUEST_DELETED = "request_deleted"  # Information request was deleted by its creator

    # Information request lifecycle events
    REQUEST_CREATED = "request_created"  # New information request submitted
    REQUEST_UPDATED = "request_updated"  # Status or content change in a request
    REQUEST_RESOLVED = "request_resolved"  # Information request marked as resolved

    # Project state and progress events
    STATUS_CHANGED = "status_changed"  # Project status or progress percentage updated
    GOAL_COMPLETED = "goal_completed"  # A project goal marked as completed
    CRITERION_COMPLETED = "criterion_completed"  # Individual success criterion achieved

    # Participant events
    PARTICIPANT_JOINED = "participant_joined"  # New team member joined the project
    PARTICIPANT_LEFT = "participant_left"  # Participant left/disconnected from project

    # Project lifecycle events
    PROJECT_STARTED = "project_started"  # Project transitioned to IN_PROGRESS state
    PROJECT_COMPLETED = "project_completed"  # Project successfully completed
    PROJECT_ABORTED = "project_aborted"  # Project terminated before completion

    # Miscellaneous events
    MILESTONE_PASSED = "milestone_passed"  # A milestone or checkpoint was passed
    INFORMATION_UPDATE = "information_update"  # General information or status update
    FILE_SHARED = "file_shared"  # A file was shared between participants
    KB_UPDATE = "kb_update"  # Whiteboard was updated
    CUSTOM = "custom"  # Custom log entry for specialized events


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


class SuccessCriterion(BaseModel):
    """
    A specific measurable criterion that defines project success.

    Success criteria are individual checkpoints that must be completed
    to achieve a project goal. Each criterion represents a concrete,
    verifiable action or condition that can be marked as completed.

    When all success criteria for all goals are completed, the project
    can be considered successful. Team members typically report when
    criteria have been met.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # Unique identifier for the criterion
    description: str  # Clear, specific description of what needs to be accomplished
    completed: bool = False  # Whether this criterion has been met
    completed_at: Optional[datetime] = None  # When the criterion was marked as completed
    completed_by: Optional[str] = None  # User ID of the person who completed the criterion


class ProjectGoal(BaseModel):
    """
    A specific goal for the project with associated success criteria.

    Project goals represent the major objectives that need to be accomplished
    for the project to be successful. Each goal consists of a name, description,
    priority level, and a list of specific success criteria that define when
    the goal can be considered complete.

    Goals are typically set by the Coordinator during project planning and then tracked
    by both the Coordinator and team members throughout the project.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # Unique identifier for the goal
    name: str  # Short, clear name of the goal
    description: str  # Detailed description of what the goal entails
    priority: int = 1  # Priority level (1 = highest priority, increasing numbers = lower priority)
    success_criteria: List[SuccessCriterion] = Field(default_factory=list)  # List of criteria to meet


class ProjectBrief(BaseEntity):
    """
    A thorough, comprehensive documentation of the project or context to be transferred,
    containing all relevant information necessary for understanding and execution.

    The project brief is the primary document that defines the project or context.
    It serves as the central reference for both the Coordinator and team members
    to understand what needs to be accomplished and why, or in the case of context transfer,
    what information needs to be preserved and communicated.

    In the standard project configuration, it includes project goals, success criteria,
    and complete context. In context transfer configuration, it focuses on capturing
    comprehensive context through detailed project_description and additional_context fields.

    Created by the Coordinator during the PLANNING phase, the brief must be
    completed before the project can move to the READY_FOR_WORKING state.
    Once team operations begin, the brief can still be updated,
    but major changes should be communicated to all participants.
    """

    project_name: str  # Short, distinctive name for the project or context transfer
    project_description: str  # Comprehensive description of the project's purpose, scope, and context
    goals: List[ProjectGoal] = Field(default_factory=list)  # List of project goals (not used in context transfer mode)
    timeline: Optional[str] = None  # Expected timeline or deadline information (not used in context transfer mode)
    additional_context: Optional[str] = (
        None  # Detailed supplementary information for project participants or context transfer
    )


class ProjectWhiteboard(BaseEntity):
    """
    A dynamic whiteboard that gets automatically updated as the coordinator assembles their project.

    The project whiteboard captures and maintains important project context that emerges during
    conversations. It is automatically updated after each assistant message by analyzing
    the conversation history and extracting key information.

    Unlike a traditional knowledge base with separate sections, the whiteboard is a single
    consolidated view that shows the most relevant information for the project. It serves as
    a dynamic, evolving source of truth that all team members can reference.
    """

    content: str = ""  # Markdown content for the whiteboard
    is_auto_generated: bool = True  # Whether the content was auto-generated or manually edited


class ProjectDashboard(BaseEntity):
    """
    A dynamic representation of progress toward success,
    updated in real time to reflect remaining tasks and progress.

    The project dashboard tracks the current state of the project and its progress.
    It provides a snapshot of how far along the project is toward completion
    and what state it's currently in (planning, in progress, etc.).

    Both the Coordinator and team members can update the project dashboard, typically with:
    - The Coordinator updating the overall state (e.g., from PLANNING to READY_FOR_WORKING)
    - Team members updating the progress percentage as they complete work

    The project dashboard is used by all project participants to understand
    the current situation and what phase the project is in.
    """

    # State of the project
    state: ProjectState = ProjectState.PLANNING  # Current project lifecycle state

    # Overall progress percentage (0-100)
    progress_percentage: int = 0

    # Copy of all goals with their current status
    goals: List[ProjectGoal] = Field(default_factory=list)

    # Active request IDs that need attention
    active_requests: List[str] = Field(default_factory=list)

    # Number of completed success criteria out of total
    completed_criteria: int = 0
    total_criteria: int = 0

    # Custom status message
    status_message: Optional[str] = None

    # Next actions or upcoming milestones
    next_actions: List[str] = Field(default_factory=list)

    # Lifecycle metadata for tracking project milestones
    lifecycle: Dict[str, Any] = Field(default_factory=dict)


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

    # Reference to the related goal(s) if applicable
    related_goal_ids: List[str] = Field(default_factory=list)  # IDs of project goals this request relates to

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
    entity_type: Optional[str] = None  # Type of related entity (e.g., "information_request", "goal")
    metadata: Optional[Dict] = None  # Additional structured data about the event


class ProjectLog(BaseEntity):
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


class ProjectInfo(BaseModel):
    """
    Core information about a project including its ID, name, and sharing details.
    
    This model stores essential project metadata that doesn't fit into other
    specific models like brief or dashboard. It's the central reference point
    for project identification and team collaboration settings.
    """
    
    project_id: str  # Unique identifier for the project
    project_name: str = "New Project"  # Name of the project
    coordinator_conversation_id: Optional[str] = None  # ID of the coordinator's conversation
    team_conversation_id: Optional[str] = None  # ID of the team workspace conversation
    share_url: Optional[str] = None  # Shareable URL for inviting users to the team workspace
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
