"""
HQ mode handler for the mission assistant.

This module provides conversation handling for HQ users in mission assistant.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from semantic_workbench_api_model.workbench_model import MessageType, NewConversationMessage
from semantic_workbench_assistant.assistant_app import ConversationContext

from .mission_data import (
    FieldRequest,
    KBSection,
    LogEntryType,
    MissionBriefing,
    MissionGoal,
    MissionKB,
    MissionState,
    MissionStatus,
    RequestStatus,
    SuccessCriterion,
)
from .mission_manager import MissionManager
from .mission_storage import (
    ConversationMissionManager,
    MissionRole,
    MissionStorage,
)
from .mission_common import log_mission_action

logger = logging.getLogger(__name__)


class HQConversationHandler:
    """
    Handler for HQ conversations in the mission assistant.
    Provides methods for managing the mission from the HQ perspective.
    """

    def __init__(self, context: ConversationContext):
        """Initialize the HQ conversation handler."""
        self.context = context

    async def initialize_mission(self, mission_name: str, mission_description: str) -> Tuple[bool, str]:
        """
        Initialize a new mission with this conversation as HQ.

        Args:
            mission_name: Name of the mission
            mission_description: Description of the mission

        Returns:
            Tuple of (success, message)
        """
        # Check if already associated with a mission
        current_mission = await ConversationMissionManager.get_conversation_mission(self.context)
        if current_mission:
            return False, f"This conversation is already associated with mission {current_mission}"

        # Create new mission with this conversation as HQ
        success, mission_id = await MissionManager.create_mission(self.context)
        if not success or not mission_id:
            return False, "Failed to create mission"
            
        # Set this conversation as HQ
        await ConversationMissionManager.set_conversation_role(self.context, mission_id, MissionRole.HQ)
            
        # Create initial mission briefing
        success, briefing = await MissionManager.create_mission_briefing(
            self.context, mission_name, mission_description
        )

        if not success or not briefing:
            return False, "Failed to initialize mission briefing"

        return True, f"Mission {mission_name} initialized with ID {mission_id}"

    async def create_mission_briefing(
        self, mission_name: str, mission_description: str, goals: Optional[List[Dict]] = None
    ) -> Tuple[bool, str, Optional[MissionBriefing]]:
        """
        Creates a mission briefing.

        Args:
            mission_name: Name of the mission
            mission_description: Description of the mission
            goals: Optional list of goals with priority and success criteria

        Returns:
            Tuple of (success, message, briefing)
        """
        # Check role
        role = await ConversationMissionManager.get_conversation_role(self.context)
        if role != MissionRole.HQ:
            return False, "Only HQ conversations can create mission briefings", None

        # Create mission briefing
        success, briefing = await MissionManager.create_mission_briefing(
            self.context, mission_name, mission_description, goals
        )

        if not success or not briefing:
            return False, "Failed to create mission briefing", None

        # Send notification
        await self.context.send_messages(
            NewConversationMessage(
                content=f"Mission briefing created for '{mission_name}'",
                message_type=MessageType.notice,
            )
        )

        return True, "Mission briefing created successfully", briefing

    async def add_mission_goal(
        self, name: str, description: str, priority: int = 1, criteria: Optional[List[str]] = None
    ) -> Tuple[bool, str, Optional[MissionBriefing]]:
        """
        Adds a goal to the mission briefing.

        Args:
            name: Name of the goal
            description: Description of the goal
            priority: Priority of the goal (1-3, with 1 being highest)
            criteria: Optional list of success criteria

        Returns:
            Tuple of (success, message, updated_briefing)
        """
        # Check role
        role = await ConversationMissionManager.get_conversation_role(self.context)
        if role != MissionRole.HQ:
            return False, "Only HQ conversations can add mission goals", None

        # Get current mission briefing
        briefing = await MissionManager.get_mission_briefing(self.context)
        if not briefing:
            return False, "No mission briefing found. Create a mission briefing first.", None

        # Create new goal
        goal = MissionGoal(
            name=name,
            description=description,
            priority=priority,
        )

        # Add success criteria if provided
        if criteria:
            for criterion in criteria:
                goal.success_criteria.append(SuccessCriterion(description=criterion))

        # Add goal to briefing
        briefing.goals.append(goal)
        briefing.updated_at = datetime.utcnow()

        # Get user ID
        participants = await self.context.get_participants()
        user_id = None
        for participant in participants.participants:
            if participant.role == "user":
                user_id = participant.id
                break

        if user_id:
            briefing.updated_by = user_id

        # Increment version
        briefing.version += 1

        # Save updated briefing
        mission_id = await ConversationMissionManager.get_conversation_mission(self.context)
        if not mission_id:
            return False, "Conversation not associated with a mission", None

        MissionStorage.write_mission_briefing(mission_id, briefing)

        # Log update
        await self.log_action(
            LogEntryType.GOAL_COMPLETED,
            f"Added mission goal: {name}",
            related_entity_id=goal.id,  # Use the new goal ID directly
        )

        # Send notification
        await self.context.send_messages(
            NewConversationMessage(
                content=f"Added mission goal: {name}",
                message_type=MessageType.notice,
            )
        )

        return True, f"Added mission goal: {name}", briefing

    async def add_kb_section(
        self, title: str, content: str, order: int = 0, tags: Optional[List[str]] = None
    ) -> Tuple[bool, str, Optional[MissionKB]]:
        """
        Adds a section to the mission knowledge base.

        Args:
            title: Title of the section
            content: Content of the section
            order: Display order (lower numbers shown first)
            tags: Optional tags for categorization

        Returns:
            Tuple of (success, message, updated_kb)
        """
        # Check role
        role = await ConversationMissionManager.get_conversation_role(self.context)
        if role != MissionRole.HQ:
            return False, "Only HQ conversations can add KB sections", None

        # Get mission ID
        mission_id = await ConversationMissionManager.get_conversation_mission(self.context)
        if not mission_id:
            return False, "Conversation not associated with a mission", None

        # Get user ID
        participants = await self.context.get_participants()
        user_id = None
        for participant in participants.participants:
            if participant.role == "user":
                user_id = participant.id
                break

        if not user_id:
            user_id = "hq-system"

        # Get existing KB or create new one
        kb = MissionStorage.read_mission_kb(mission_id)

        if not kb:
            # Create new KB
            kb = MissionKB(
                created_by=user_id,
                updated_by=user_id,
                conversation_id=str(self.context.id),
                sections={},
            )

        # Create section
        section = KBSection(
            title=title,
            content=content,
            order=order,
            tags=tags or [],
            updated_by=user_id,
        )

        # Add to KB
        kb.sections[section.id] = section
        kb.updated_at = datetime.utcnow()
        kb.updated_by = user_id
        kb.version += 1

        # Save KB
        MissionStorage.write_mission_kb(mission_id, kb)

        # Log update
        await self.log_action(
            LogEntryType.KB_UPDATE,
            f"Added KB section: {title}",
            related_entity_id=section.id,  # Use the section ID directly
        )

        # Send notification
        await self.context.send_messages(
            NewConversationMessage(
                content=f"Added knowledge base section: {title}",
                message_type=MessageType.notice,
            )
        )

        return True, f"Added knowledge base section: {title}", kb

    async def resolve_field_request(self, request_id: str, resolution: str) -> Tuple[bool, str, Optional[FieldRequest]]:
        """
        Resolves a field request.

        Args:
            request_id: ID of the request to resolve
            resolution: Resolution information

        Returns:
            Tuple of (success, message, resolved_request)
        """
        # Check role
        role = await ConversationMissionManager.get_conversation_role(self.context)
        if role != MissionRole.HQ:
            return False, "Only HQ conversations can resolve field requests", None

        # Get mission ID
        mission_id = await ConversationMissionManager.get_conversation_mission(self.context)
        if not mission_id:
            return False, "Conversation not associated with a mission", None

        # Find the request
        request = MissionStorage.read_field_request(mission_id, request_id)

        if not request:
            return False, f"Field request {request_id} not found", None

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
            user_id = "hq-system"

        request.resolved_by = user_id
        request.updated_at = datetime.utcnow()
        request.updated_by = user_id
        request.version += 1

        # Save updated request
        MissionStorage.write_field_request(mission_id, request)

        # Log resolution
        await self.log_action(
            LogEntryType.REQUEST_RESOLVED,
            f"Resolved field request: {request.title}",
            related_entity_id=request_id,
            additional_metadata={
                "resolution": resolution,
                "requester_id": request.created_by,  # Use created_by as requester
            },
        )

        # Update mission status if this was a blocker
        status = await MissionManager.get_mission_status(self.context)
        if status and request_id in status.active_blockers:
            status.active_blockers.remove(request_id)
            status.updated_at = datetime.utcnow()
            status.updated_by = user_id
            status.version += 1

            MissionStorage.write_mission_status(mission_id, status)

        # Send notification
        await self.context.send_messages(
            NewConversationMessage(
                content=f"Resolved field request: {request.title}",
                message_type=MessageType.notice,
            )
        )

        return True, f"Resolved field request: {request.title}", request

    async def mark_mission_ready_for_field(self) -> Tuple[bool, str, Optional[MissionStatus]]:
        """
        Marks the mission as ready for field operations.

        Returns:
            Tuple of (success, message, updated_status)
        """
        # Check role
        role = await ConversationMissionManager.get_conversation_role(self.context)
        if role != MissionRole.HQ:
            return False, "Only HQ conversations can mark missions as ready for field", None

        # Get mission ID and status
        mission_id = await ConversationMissionManager.get_conversation_mission(self.context)
        if not mission_id:
            return False, "Conversation not associated with a mission", None

        status = await MissionManager.get_mission_status(self.context)
        if not status:
            return False, "Mission status not found", None

        # Update status
        status.state = MissionState.READY_FOR_FIELD
        status.updated_at = datetime.utcnow()

        # Get user info
        participants = await self.context.get_participants()
        user_id = None
        for participant in participants.participants:
            if participant.role == "user":
                user_id = participant.id
                break

        if not user_id:
            user_id = "hq-system"

        status.updated_by = user_id
        status.version += 1

        # Save updated status
        MissionStorage.write_mission_status(mission_id, status)

        # Log the gate passage
        await self.log_action(
            LogEntryType.GATE_PASSED,
            "Mission marked as ready for field operations",
            related_entity_id=None,  # No specific entity ID needed
            additional_metadata={
                "previous_state": MissionState.PLANNING.value,
                "new_state": MissionState.READY_FOR_FIELD.value,
            },
        )

        # Send notification
        await self.context.send_messages(
            NewConversationMessage(
                content="Mission has been marked as ready for field operations",
                message_type=MessageType.notice,
            )
        )

        return True, "Mission marked as ready for field operations", status

    async def get_mission_info(self) -> Dict:
        """
        Gets information about the mission.

        Returns:
            Dictionary with mission information
        """
        mission_id = await ConversationMissionManager.get_conversation_mission(self.context)
        if not mission_id:
            return {
                "has_mission": False,
                "message": "This conversation is not associated with a mission",
            }

        role = await ConversationMissionManager.get_conversation_role(self.context)

        briefing = await MissionManager.get_mission_briefing(self.context)
        status = await MissionManager.get_mission_status(self.context)

        # Get field requests
        requests = await MissionManager.get_field_requests(self.context)
        open_requests_count = len(requests)

        # Additional info for HQ users
        pending_invitations = []
        if role == MissionRole.HQ:
            # Skip invitation handling for now as part of the refactoring
            # This can be re-implemented once we have a proper invitation system in place
            pending_invitations = []

        return {
            "has_mission": True,
            "mission_id": mission_id,
            "role": role.value if role else None,
            "mission_name": briefing.mission_name if briefing else "Unnamed Mission",
            "mission_description": briefing.mission_description if briefing else "",
            "status": status.state.value if status else "unknown",
            "progress": status.progress_percentage if status else 0,
            "open_requests": open_requests_count,
            "pending_invitations": pending_invitations if role == MissionRole.HQ else [],
        }

    async def log_action(
        self,
        entry_type: LogEntryType,
        message: str,
        related_entity_id: Optional[str] = None,
        additional_metadata: Optional[Dict] = None,
    ) -> None:
        """
        Logs an action to the mission log.

        Args:
            entry_type: Type of log entry
            message: Message to log
            related_entity_id: Optional ID of related entity
            additional_metadata: Optional additional metadata
        """
        await log_mission_action(
            context=self.context,
            entry_type=entry_type,
            message=message,
            related_entity_id=related_entity_id,
            additional_metadata=additional_metadata,
        )
