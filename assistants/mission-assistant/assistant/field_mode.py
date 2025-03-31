"""
Field mode handler for the mission assistant.

This module provides conversation handling for Field users in mission assistant.
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Tuple

from semantic_workbench_api_model.workbench_model import MessageType, NewConversationMessage
from semantic_workbench_assistant.assistant_app import ConversationContext

from .artifacts import (
    ArtifactType,
    FieldRequest,
    LogEntry,
    LogEntryType,
    MissionKB,
    MissionLog,
    MissionState,
    MissionStatus,
    RequestPriority,
    RequestStatus,
)
from .mission_manager import MissionManager, MissionRole
from .mission_storage import (
    ConversationMissionManager,
    MissionStorageReader,
    MissionStorageWriter,
)

logger = logging.getLogger(__name__)


class FieldConversationHandler:
    """
    Handler for Field conversations in the mission assistant.
    Provides methods for participating in missions from the Field perspective.
    """
    
    def __init__(self, context: ConversationContext):
        """Initialize the Field conversation handler."""
        self.context = context
    
    async def create_field_request(
        self, title: str, description: str, priority: RequestPriority = RequestPriority.MEDIUM
    ) -> Tuple[bool, str, Optional[FieldRequest]]:
        """
        Creates a field request for assistance from HQ.
        
        Args:
            title: Title of the request
            description: Detailed description of the request
            priority: Priority level of the request
            
        Returns:
            Tuple of (success, message, request)
        """
        # Check role
        role = await MissionManager.get_conversation_role(self.context)
        if role != MissionRole.FIELD:
            return False, "Only Field conversations can create field requests", None
        
        # Get mission ID
        mission_id = await ConversationMissionManager.get_conversation_mission(self.context)
        if not mission_id:
            return False, "Conversation not associated with a mission", None
        
        # Get user info
        participants = await self.context.get_participants()
        user_id = None
        for participant in participants.participants:
            if participant.role == "user":
                user_id = participant.id
                break
        
        if not user_id:
            user_id = "field-system"
        
        # Create request
        request = FieldRequest(
            artifact_type=ArtifactType.FIELD_REQUEST,
            title=title,
            description=description,
            priority=priority,
            status=RequestStatus.NEW,
            created_by=user_id,
            updated_by=user_id,
            conversation_id=str(self.context.id)
        )
        
        # Save request
        MissionStorageWriter.write_artifact(
            mission_id=mission_id,
            artifact_type=ArtifactType.FIELD_REQUEST.value,
            artifact_id=request.artifact_id,
            artifact=request
        )
        
        # Log the request creation
        await self.log_action(
            LogEntryType.REQUEST_CREATED,
            f"Created field request: {title}",
            artifact_id=request.artifact_id,
            artifact_type=ArtifactType.FIELD_REQUEST
        )
        
        # Update mission status to include this request as a potential blocker
        status = await MissionManager.get_mission_status(self.context)
        if status and priority in [RequestPriority.HIGH, RequestPriority.CRITICAL] and request.artifact_id:
            status.active_blockers.append(request.artifact_id)
            status.updated_at = datetime.utcnow()
            status.updated_by = user_id
            status.version += 1
            
            MissionStorageWriter.write_artifact(
                mission_id=mission_id,
                artifact_type=ArtifactType.MISSION_STATUS.value,
                artifact_id=status.artifact_id,
                artifact=status
            )
        
        # Send notification
        await self.context.send_messages(
            NewConversationMessage(
                content=f"Created field request: {title}",
                message_type=MessageType.notice,
            )
        )
        
        return True, f"Created field request: {title}", request
    
    async def update_mission_status(
        self, progress_percentage: int, status_message: Optional[str] = None
    ) -> Tuple[bool, str, Optional[MissionStatus]]:
        """
        Updates the mission status with progress information from the field.
        
        Args:
            progress_percentage: Current mission progress percentage (0-100)
            status_message: Optional status message or update from field
            
        Returns:
            Tuple of (success, message, updated_status)
        """
        # Check role
        role = await MissionManager.get_conversation_role(self.context)
        if role != MissionRole.FIELD:
            return False, "Only Field conversations can update mission status", None
        
        # Get mission ID
        mission_id = await ConversationMissionManager.get_conversation_mission(self.context)
        if not mission_id:
            return False, "Conversation not associated with a mission", None
        
        # Get status
        status = await MissionManager.get_mission_status(self.context)
        if not status:
            return False, "Mission status not found", None
        
        # Make sure mission is in the right state for field updates
        if status.state not in [MissionState.READY_FOR_FIELD, MissionState.IN_PROGRESS]:
            return False, f"Cannot update mission in {status.state} state. Mission must be ready for field operations.", None
        
        # Get user info
        participants = await self.context.get_participants()
        user_id = None
        for participant in participants.participants:
            if participant.role == "user":
                user_id = participant.id
                break
        
        if not user_id:
            user_id = "field-system"
        
        # Update status
        previous_progress = status.progress_percentage
        status.progress_percentage = max(0, min(100, progress_percentage))  # Clamp between 0-100
        if status_message:
            status.status_message = status_message
        
        # If this is the first field update, change state to IN_PROGRESS
        if status.state == MissionState.READY_FOR_FIELD:
            previous_state = status.state
            status.state = MissionState.IN_PROGRESS
            
            # Log state change
            await self.log_action(
                LogEntryType.GATE_PASSED,
                "Mission is now in progress",
                artifact_id=status.artifact_id,
                artifact_type=ArtifactType.MISSION_STATUS,
                additional_metadata={
                    "previous_state": previous_state.value,
                    "new_state": MissionState.IN_PROGRESS.value,
                }
            )
        
        status.updated_at = datetime.utcnow()
        status.updated_by = user_id
        status.version += 1
        
        # Save updated status
        MissionStorageWriter.write_artifact(
            mission_id=mission_id,
            artifact_type=ArtifactType.MISSION_STATUS.value,
            artifact_id=status.artifact_id,
            artifact=status
        )
        
        # Log update
        await self.log_action(
            LogEntryType.STATUS_CHANGED,
            f"Updated mission progress to {progress_percentage}%",
            artifact_id=status.artifact_id,
            artifact_type=ArtifactType.MISSION_STATUS,
            additional_metadata={
                "previous_progress": previous_progress,
                "new_progress": progress_percentage,
                "status_message": status_message,
            }
        )
        
        # Send notification
        await self.context.send_messages(
            NewConversationMessage(
                content=f"Updated mission progress to {progress_percentage}%",
                message_type=MessageType.notice,
            )
        )
        
        return True, f"Updated mission progress to {progress_percentage}%", status
    
    async def mark_criterion_completed(
        self, goal_id: str, criterion_id: str
    ) -> Tuple[bool, str, Optional[MissionStatus]]:
        """
        Marks a success criterion as completed.
        
        Args:
            goal_id: ID of the goal containing the criterion
            criterion_id: ID of the criterion to mark completed
            
        Returns:
            Tuple of (success, message, updated_status)
        """
        # Check role
        role = await MissionManager.get_conversation_role(self.context)
        if role != MissionRole.FIELD:
            return False, "Only Field conversations can mark criteria as completed", None
        
        # Get mission ID
        mission_id = await ConversationMissionManager.get_conversation_mission(self.context)
        if not mission_id:
            return False, "Conversation not associated with a mission", None
        
        # Get briefing
        briefing = await MissionManager.get_mission_briefing(self.context)
        if not briefing:
            return False, "Mission briefing not found", None
        
        # Find the goal and criterion
        goal = None
        criterion = None
        for g in briefing.goals:
            if g.id == goal_id:
                goal = g
                for c in g.success_criteria:
                    if c.id == criterion_id:
                        criterion = c
                        break
                break
        
        if not goal:
            return False, f"Goal {goal_id} not found", None
        
        if not criterion:
            return False, f"Criterion {criterion_id} not found in goal {goal.name}", None
        
        if criterion.completed:
            return True, f"Criterion '{criterion.description}' was already marked as completed", None
        
        # Get user info
        participants = await self.context.get_participants()
        user_id = None
        for participant in participants.participants:
            if participant.role == "user":
                user_id = participant.id
                break
        
        if not user_id:
            user_id = "field-system"
        
        # Update criterion
        criterion.completed = True
        criterion.completed_at = datetime.utcnow()
        criterion.completed_by = user_id
        
        # Save updated briefing
        briefing.updated_at = datetime.utcnow()
        briefing.updated_by = user_id
        briefing.version += 1
        
        MissionStorageWriter.write_artifact(
            mission_id=mission_id,
            artifact_type=ArtifactType.MISSION_BRIEFING.value,
            artifact_id=briefing.artifact_id,
            artifact=briefing
        )
        
        # Update mission status
        status = await MissionManager.get_mission_status(self.context)
        if not status:
            return False, "Mission status not found", None
        
        # Count completed criteria
        total_criteria = 0
        completed_criteria = 0
        for g in briefing.goals:
            total_criteria += len(g.success_criteria)
            completed_criteria += sum(1 for c in g.success_criteria if c.completed)
        
        # Update status
        status.completed_criteria = completed_criteria
        status.total_criteria = total_criteria
        
        # Calculate progress percentage based on completed criteria
        if total_criteria > 0:
            status.progress_percentage = int((completed_criteria / total_criteria) * 100)
        
        status.updated_at = datetime.utcnow()
        status.updated_by = user_id
        status.version += 1
        
        # Save updated status
        MissionStorageWriter.write_artifact(
            mission_id=mission_id,
            artifact_type=ArtifactType.MISSION_STATUS.value,
            artifact_id=status.artifact_id,
            artifact=status
        )
        
        # Log completion
        await self.log_action(
            LogEntryType.CRITERION_COMPLETED,
            f"Completed criterion: {criterion.description}",
            artifact_id=criterion_id,
            artifact_type=ArtifactType.MISSION_BRIEFING,
            additional_metadata={
                "goal_id": goal_id,
                "goal_name": goal.name,
                "progress": status.progress_percentage,
            }
        )
        
        # Check if all goals are completed
        all_complete = all(
            all(c.completed for c in g.success_criteria) 
            for g in briefing.goals 
            if g.success_criteria
        )
        
        if all_complete and status.state != MissionState.COMPLETED:
            # Mark mission as completed
            status.state = MissionState.COMPLETED
            status.progress_percentage = 100
            status.status_message = "All success criteria have been met"
            status.updated_at = datetime.utcnow()
            status.updated_by = user_id
            status.version += 1
            
            MissionStorageWriter.write_artifact(
                mission_id=mission_id,
                artifact_type=ArtifactType.MISSION_STATUS.value,
                artifact_id=status.artifact_id,
                artifact=status
            )
            
            # Log mission completion
            await self.log_action(
                LogEntryType.MISSION_COMPLETED,
                "Mission completed successfully",
                artifact_id=status.artifact_id,
                artifact_type=ArtifactType.MISSION_STATUS,
            )
            
            # Send notification
            await self.context.send_messages(
                NewConversationMessage(
                    content="🎉 Mission completed! All success criteria have been met.",
                    message_type=MessageType.notice,
                )
            )
        else:
            # Send notification
            await self.context.send_messages(
                NewConversationMessage(
                    content=f"Marked criterion '{criterion.description}' as completed.",
                    message_type=MessageType.notice,
                )
            )
        
        return True, f"Marked criterion '{criterion.description}' as completed.", status
    
    async def report_mission_completed(
        self, completion_summary: str
    ) -> Tuple[bool, str, Optional[MissionStatus]]:
        """
        Reports that the mission has been completed from the field perspective.
        
        Args:
            completion_summary: Summary of the mission completion
            
        Returns:
            Tuple of (success, message, updated_status)
        """
        # Check role
        role = await MissionManager.get_conversation_role(self.context)
        if role != MissionRole.FIELD:
            return False, "Only Field conversations can report mission completion", None
        
        # Get mission ID
        mission_id = await ConversationMissionManager.get_conversation_mission(self.context)
        if not mission_id:
            return False, "Conversation not associated with a mission", None
        
        # Get status
        status = await MissionManager.get_mission_status(self.context)
        if not status:
            return False, "Mission status not found", None
        
        # Get user info
        participants = await self.context.get_participants()
        user_id = None
        for participant in participants.participants:
            if participant.role == "user":
                user_id = participant.id
                break
        
        if not user_id:
            user_id = "field-system"
        
        # Update status
        previous_state = status.state
        status.state = MissionState.COMPLETED
        status.progress_percentage = 100
        status.status_message = completion_summary
        status.updated_at = datetime.utcnow()
        status.updated_by = user_id
        status.version += 1
        
        # Save updated status
        MissionStorageWriter.write_artifact(
            mission_id=mission_id,
            artifact_type=ArtifactType.MISSION_STATUS.value,
            artifact_id=status.artifact_id,
            artifact=status
        )
        
        # Log mission completion
        await self.log_action(
            LogEntryType.MISSION_COMPLETED,
            "Mission marked as completed",
            artifact_id=status.artifact_id,
            artifact_type=ArtifactType.MISSION_STATUS,
            additional_metadata={
                "previous_state": previous_state.value,
                "completion_summary": completion_summary,
            }
        )
        
        # Send notification
        await self.context.send_messages(
            NewConversationMessage(
                content="🎉 Mission has been marked as completed.",
                message_type=MessageType.notice,
            )
        )
        
        return True, "Mission has been marked as completed", status
    
    async def get_kb_section(self, section_id: Optional[str] = None) -> Dict:
        """
        Retrieves knowledge base content from mission KB.
        
        Args:
            section_id: Optional ID of specific section to retrieve
            
        Returns:
            Dictionary with KB information
        """
        mission_id = await ConversationMissionManager.get_conversation_mission(self.context)
        if not mission_id:
            return {
                "has_kb": False,
                "message": "This conversation is not associated with a mission",
            }
        
        # Get KB
        kb_list = MissionStorageReader.read_all_artifacts(
            mission_id=mission_id,
            artifact_type=ArtifactType.KNOWLEDGE_BASE.value,
            model_class=MissionKB
        )
        
        if not kb_list:
            return {
                "has_kb": False,
                "message": "No knowledge base found for this mission",
            }
        
        # Use the most recent KB
        kb = kb_list[0]
        
        # If section ID provided, return just that section
        if section_id and section_id in kb.sections:
            section = kb.sections[section_id]
            return {
                "has_kb": True,
                "sections": [
                    {
                        "id": section.id,
                        "title": section.title,
                        "content": section.content,
                        "tags": section.tags,
                        "last_updated": section.last_updated.isoformat(),
                    }
                ],
            }
        
        # Otherwise return all sections, sorted by order
        sorted_sections = sorted(kb.sections.values(), key=lambda s: s.order)
        return {
            "has_kb": True,
            "sections": [
                {
                    "id": section.id,
                    "title": section.title,
                    "content": section.content,
                    "tags": section.tags,
                    "last_updated": section.last_updated.isoformat(),
                }
                for section in sorted_sections
            ],
        }
    
    async def get_mission_briefing_info(self) -> Dict:
        """
        Gets information about the mission briefing.
        
        Returns:
            Dictionary with briefing information
        """
        briefing = await MissionManager.get_mission_briefing(self.context)
        if not briefing:
            return {
                "has_briefing": False,
                "message": "No mission briefing found",
            }
        
        return {
            "has_briefing": True,
            "mission_name": briefing.mission_name,
            "mission_description": briefing.mission_description,
            "goals": [
                {
                    "id": goal.id,
                    "name": goal.name,
                    "description": goal.description,
                    "priority": goal.priority,
                    "success_criteria": [
                        {
                            "id": criterion.id,
                            "description": criterion.description,
                            "completed": criterion.completed,
                            "completed_at": criterion.completed_at.isoformat() if criterion.completed_at else None,
                        }
                        for criterion in goal.success_criteria
                    ],
                }
                for goal in briefing.goals
            ],
            "timeline": briefing.timeline,
            "additional_context": briefing.additional_context,
        }
    
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
        
        role = await MissionManager.get_conversation_role(self.context)
        
        briefing = await MissionManager.get_mission_briefing(self.context)
        status = await MissionManager.get_mission_status(self.context)
        
        # Get field requests made by this conversation
        requests = await MissionManager.get_field_requests(self.context)
        my_requests = [r for r in requests if r.conversation_id == str(self.context.id)]
        open_requests_count = len(my_requests)
        
        return {
            "has_mission": True,
            "mission_id": mission_id,
            "role": role.value if role else None,
            "mission_name": briefing.mission_name if briefing else "Unnamed Mission",
            "mission_description": briefing.mission_description if briefing else "",
            "status": status.state.value if status else "unknown",
            "progress": status.progress_percentage if status else 0,
            "open_requests": open_requests_count,
            "pending_requests": [
                {
                    "id": req.artifact_id,
                    "title": req.title,
                    "status": req.status,
                    "priority": req.priority,
                    "created_at": req.created_at.isoformat(),
                }
                for req in my_requests
                if req.status != RequestStatus.RESOLVED
            ],
        }
    
    async def log_action(
        self,
        entry_type: LogEntryType,
        message: str,
        artifact_id: Optional[str] = None,
        artifact_type: Optional[ArtifactType] = None,
        additional_metadata: Optional[Dict] = None,
    ) -> None:
        """
        Logs an action to the mission log.
        
        Args:
            entry_type: Type of log entry
            message: Message to log
            related_artifact_id: Optional ID of related artifact
            related_artifact_type: Optional type of related artifact
            additional_metadata: Optional additional metadata
        """
        mission_id = await ConversationMissionManager.get_conversation_mission(self.context)
        if not mission_id:
            return
        
        # Get user info
        participants = await self.context.get_participants()
        user_id = None
        user_name = "Field User"  # We need to keep this for the LogEntry
        for participant in participants.participants:
            if participant.role == "user":
                user_id = participant.id
                user_name = participant.name
                break
        
        if not user_id:
            user_id = "field-system"
        
        # Get mission log
        logs = MissionStorageReader.read_all_artifacts(
            mission_id=mission_id,
            artifact_type=ArtifactType.MISSION_LOG.value,
            model_class=MissionLog
        )
        
        log = None
        if logs:
            log = logs[0]  # Use the first log
        else:
            # Create new log
            log = MissionLog(
                artifact_type=ArtifactType.MISSION_LOG,
                created_by=user_id,
                updated_by=user_id,
                conversation_id=str(self.context.id),
                entries=[]
            )
        
        # Create log entry
        entry = LogEntry(
            entry_type=entry_type,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            user_name=user_name,
            message=message,
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            metadata=additional_metadata or {},
        )
        
        # Add entry to log
        log.entries.append(entry)
        log.updated_at = datetime.utcnow()
        log.updated_by = user_id
        log.version += 1
        
        # Save log
        MissionStorageWriter.write_artifact(
            mission_id=mission_id,
            artifact_type=ArtifactType.MISSION_LOG.value,
            artifact_id=log.artifact_id,
            artifact=log
        )