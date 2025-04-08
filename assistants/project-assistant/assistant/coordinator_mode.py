"""
Coordinator mode handler for the project assistant.

This module provides conversation handling for Coordinator users in project assistant.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from semantic_workbench_api_model.workbench_model import MessageType, NewConversationMessage
from semantic_workbench_assistant.assistant_app import ConversationContext

from .project_common import log_project_action
from .project_data import (
    InformationRequest,
    LogEntryType,
    ProjectBrief,
    ProjectDashboard,
    ProjectGoal,
    ProjectState,
    RequestStatus,
    SuccessCriterion,
)
from .project_manager import ProjectManager
from .project_storage import (
    ConversationProjectManager,
    ProjectRole,
    ProjectStorage,
)

logger = logging.getLogger(__name__)


class CoordinatorConversationHandler:
    """
    Handler for Coordinator conversations in the project assistant.
    Provides methods for managing the project from the Coordinator perspective.
    """

    def __init__(self, context: ConversationContext):
        """Initialize the Coordinator conversation handler."""
        self.context = context

    async def handle_project_update(
        self, update_type: str, message: str, data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Handles project update notifications in Coordinator conversations.

        Args:
            update_type: Type of update
            message: Notification message
            data: Additional data about the update

        Returns:
            True if handled successfully, False otherwise
        """
        # Get project ID
        project_id = await ConversationProjectManager.get_conversation_project(self.context)
        if not project_id:
            return False

        # First verify this is a Coordinator conversation
        role = await ConversationProjectManager.get_conversation_role(self.context)
        if role != ProjectRole.COORDINATOR:
            return False  # Not a Coordinator conversation, skip handling

        # Currently no specific handling needed for Coordinator, but this method
        # provides a hook for future enhancements

        return False  # No update types currently handled by Coordinator

    async def initialize_project(self, project_name: str, project_description: str) -> Tuple[bool, str]:
        """
        Initialize a new project with this conversation as Coordinator.

        Args:
            project_name: Name of the project
            project_description: Description of the project

        Returns:
            Tuple of (success, message)
        """
        # Check if already associated with a project
        current_project = await ConversationProjectManager.get_conversation_project(self.context)
        if current_project:
            return False, f"This conversation is already associated with project {current_project}"

        # Create new project with this conversation as Coordinator
        success, project_id = await ProjectManager.create_project(self.context)
        if not success or not project_id:
            return False, "Failed to create project"

        # Set this conversation as Coordinator
        await ConversationProjectManager.set_conversation_role(self.context, project_id, ProjectRole.COORDINATOR)

        # Create initial project brief
        success, brief = await ProjectManager.create_project_brief(self.context, project_name, project_description)

        if not success or not brief:
            return False, "Failed to initialize project brief"

        return True, f"Project {project_name} initialized with ID {project_id}"

    async def create_project_brief(
        self, project_name: str, project_description: str, goals: Optional[List[Dict]] = None
    ) -> Tuple[bool, str, Optional[ProjectBrief]]:
        """
        Creates a project brief.

        Args:
            project_name: Name of the project
            project_description: Description of the project
            goals: Optional list of goals with priority and success criteria

        Returns:
            Tuple of (success, message, brief)
        """
        # Check role
        role = await ConversationProjectManager.get_conversation_role(self.context)
        if role != ProjectRole.COORDINATOR:
            return False, "Only Coordinator conversations can create project briefs", None

        # Create project brief
        success, brief = await ProjectManager.create_project_brief(
            self.context, project_name, project_description, goals
        )

        if not success or not brief:
            return False, "Failed to create project brief", None

        # Send notification
        await self.context.send_messages(
            NewConversationMessage(
                content=f"Project brief created for '{project_name}'",
                message_type=MessageType.notice,
            )
        )

        return True, "Project brief created successfully", brief

    async def add_project_goal(
        self, name: str, description: str, priority: int = 1, criteria: Optional[List[str]] = None
    ) -> Tuple[bool, str, Optional[ProjectBrief]]:
        """
        Adds a goal to the project brief.

        Args:
            name: Name of the goal
            description: Description of the goal
            priority: Priority of the goal (1-3, with 1 being highest)
            criteria: Optional list of success criteria

        Returns:
            Tuple of (success, message, updated_brief)
        """
        # Check role
        role = await ConversationProjectManager.get_conversation_role(self.context)
        if role != ProjectRole.COORDINATOR:
            return False, "Only Coordinator conversations can add project goals", None

        # Get current project brief
        brief = await ProjectManager.get_project_brief(self.context)
        if not brief:
            return False, "No project brief found. Create a project brief first.", None

        # Create new goal
        goal = ProjectGoal(
            name=name,
            description=description,
            priority=priority,
        )

        # Add success criteria if provided
        if criteria:
            for criterion in criteria:
                goal.success_criteria.append(SuccessCriterion(description=criterion))

        # Add goal to brief
        brief.goals.append(goal)
        brief.updated_at = datetime.utcnow()

        # Get user ID
        participants = await self.context.get_participants()
        user_id = None
        for participant in participants.participants:
            if participant.role == "user":
                user_id = participant.id
                break

        if user_id:
            brief.updated_by = user_id

        # Increment version
        brief.version += 1

        # Save updated brief
        project_id = await ConversationProjectManager.get_conversation_project(self.context)
        if not project_id:
            return False, "Conversation not associated with a project", None

        ProjectStorage.write_project_brief(project_id, brief)

        # Log update
        await self.log_action(
            LogEntryType.GOAL_COMPLETED,
            f"Added project goal: {name}",
            related_entity_id=goal.id,  # Use the new goal ID directly
        )

        # Send notification
        await self.context.send_messages(
            NewConversationMessage(
                content=f"Added project goal: {name}",
                message_type=MessageType.notice,
            )
        )

        return True, f"Added project goal: {name}", brief

    async def resolve_information_request(
        self, request_id: str, resolution: str
    ) -> Tuple[bool, str, Optional[InformationRequest]]:
        """
        Resolves an information request.

        Args:
            request_id: ID of the request to resolve
            resolution: Resolution information

        Returns:
            Tuple of (success, message, resolved_request)
        """
        # Check role
        role = await ConversationProjectManager.get_conversation_role(self.context)
        if role != ProjectRole.COORDINATOR:
            return False, "Only Coordinator conversations can resolve information requests", None

        # Get project ID
        project_id = await ConversationProjectManager.get_conversation_project(self.context)
        if not project_id:
            return False, "Conversation not associated with a project", None

        # Find the request
        request = ProjectStorage.read_information_request(project_id, request_id)

        if not request:
            return False, f"Information request {request_id} not found", None

        # Update request
        request.status = RequestStatus.RESOLVED
        request.resolution = resolution
        request.resolved_at = datetime.utcnow()

        # Get user info
        participants = await self.context.get_participants()
        user_id = None
        for participant in participants.participants:
            if participant.role == "user":
                user_id = participant.id
                break

        if not user_id:
            user_id = "coordinator-system"

        request.resolved_by = user_id
        request.updated_at = datetime.utcnow()
        request.updated_by = user_id
        request.version += 1

        # Save updated request
        ProjectStorage.write_information_request(project_id, request)

        # Log resolution
        await self.log_action(
            LogEntryType.REQUEST_RESOLVED,
            f"Resolved information request: {request.title}",
            related_entity_id=request_id,
            additional_metadata={
                "resolution": resolution,
                "requester_id": request.created_by,  # Use created_by as requester
            },
        )

        # Update project dashboard if this was a blocker
        dashboard = await ProjectManager.get_project_dashboard(self.context)
        if dashboard and request_id in dashboard.active_blockers:
            dashboard.active_blockers.remove(request_id)
            dashboard.updated_at = datetime.utcnow()
            dashboard.updated_by = user_id
            dashboard.version += 1

            ProjectStorage.write_project_dashboard(project_id, dashboard)

        # Send notification
        await self.context.send_messages(
            NewConversationMessage(
                content=f"Resolved information request: {request.title}",
                message_type=MessageType.notice,
            )
        )

        return True, f"Resolved information request: {request.title}", request

    async def mark_project_ready_for_working(self) -> Tuple[bool, str, Optional[ProjectDashboard]]:
        """
        Marks the project as ready for team operations.

        Returns:
            Tuple of (success, message, updated_dashboard)
        """
        # Check role
        role = await ConversationProjectManager.get_conversation_role(self.context)
        if role != ProjectRole.COORDINATOR:
            return False, "Only Coordinator conversations can mark projects as ready for team work", None

        # Get project ID and dashboard
        project_id = await ConversationProjectManager.get_conversation_project(self.context)
        if not project_id:
            return False, "Conversation not associated with a project", None

        dashboard = await ProjectManager.get_project_dashboard(self.context)
        if not dashboard:
            return False, "Project dashboard not found", None

        # Update dashboard
        dashboard.state = ProjectState.READY_FOR_WORKING
        dashboard.updated_at = datetime.utcnow()

        # Get user info
        participants = await self.context.get_participants()
        user_id = None
        for participant in participants.participants:
            if participant.role == "user":
                user_id = participant.id
                break

        if not user_id:
            user_id = "coordinator-system"

        dashboard.updated_by = user_id
        dashboard.version += 1

        # Save updated dashboard
        ProjectStorage.write_project_dashboard(project_id, dashboard)

        # Log the milestone passage
        await self.log_action(
            LogEntryType.MILESTONE_PASSED,
            "Project marked as ready for team operations",
            related_entity_id=None,  # No specific entity ID needed
            additional_metadata={
                "previous_state": ProjectState.PLANNING.value,
                "new_state": ProjectState.READY_FOR_WORKING.value,
            },
        )

        # Send notification
        await self.context.send_messages(
            NewConversationMessage(
                content="Project has been marked as ready for team operations",
                message_type=MessageType.notice,
            )
        )

        return True, "Project marked as ready for team operations", dashboard

    async def get_project_info(self) -> Dict:
        """
        Gets information about the project.

        Returns:
            Dictionary with project information
        """
        project_id = await ConversationProjectManager.get_conversation_project(self.context)
        if not project_id:
            return {
                "has_project": False,
                "message": "This conversation is not associated with a project",
            }

        role = await ConversationProjectManager.get_conversation_role(self.context)

        brief = await ProjectManager.get_project_brief(self.context)
        dashboard = await ProjectManager.get_project_dashboard(self.context)

        # Get information requests
        requests = await ProjectManager.get_information_requests(self.context)
        open_requests_count = len(requests)

        # Additional info for Coordinator users
        pending_invitations = []
        if role == ProjectRole.COORDINATOR:
            # Skip invitation handling for now as part of the refactoring
            # This can be re-implemented once we have a proper invitation system in place
            pending_invitations = []

        return {
            "has_project": True,
            "project_id": project_id,
            "role": role.value if role else None,
            "project_name": brief.project_name if brief else "Unnamed Project",
            "project_description": brief.project_description if brief else "",
            "status": dashboard.state.value if dashboard else "unknown",
            "progress": dashboard.progress_percentage if dashboard else 0,
            "open_requests": open_requests_count,
            "pending_invitations": pending_invitations if role == ProjectRole.COORDINATOR else [],
        }

    async def log_action(
        self,
        entry_type: LogEntryType,
        message: str,
        related_entity_id: Optional[str] = None,
        additional_metadata: Optional[Dict] = None,
    ) -> None:
        """
        Logs an action to the project log.

        Args:
            entry_type: Type of log entry
            message: Message to log
            related_entity_id: Optional ID of related entity
            additional_metadata: Optional additional metadata
        """
        await log_project_action(
            context=self.context,
            entry_type=entry_type,
            message=message,
            related_entity_id=related_entity_id,
            additional_metadata=additional_metadata,
        )
