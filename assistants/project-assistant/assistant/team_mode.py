"""
Team mode handler for the project assistant.

This module provides conversation handling for Team members in project assistant.
"""

from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from semantic_workbench_api_model.workbench_model import MessageType, NewConversationMessage
from semantic_workbench_assistant.assistant_app import ConversationContext

from .logging import logger
from .project_common import ConversationRole, detect_assistant_role, log_project_action
from .project_data import (
    InformationRequest,
    LogEntryType,
    ProjectInfo,
    ProjectState,
    RequestPriority,
    RequestStatus,
)
from .project_manager import ProjectManager
from .project_storage import (
    ConversationProjectManager,
    ProjectStorage,
)

# logger is now imported from .logging


class TeamConversationHandler:
    """
    Handler for Team conversations in the project assistant.
    Provides methods for participating in projects from the Team member perspective.
    """

    def __init__(self, context: ConversationContext):
        """Initialize the Team conversation handler."""
        self.context = context

    async def handle_project_update(
        self, update_type: str, message: str, data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Handles project update notifications in Team conversations.

        Args:
            update_type: Type of update (e.g., 'file_created', 'file_updated', 'file_deleted')
            message: Notification message
            data: Additional data about the update

        Returns:
            True if handled successfully, False otherwise
        """
        # Log update details
        logger.info(f"Team received project update: type={update_type}, message='{message}', data={data}")

        # Get project ID
        project_id = await ConversationProjectManager.get_associated_project_id(self.context)
        if not project_id:
            logger.warning("No project ID found for this conversation, cannot process update")
            return False

        # First verify this is a Team conversation
        role = await detect_assistant_role(self.context)
        
        if role != ConversationRole.TEAM:
            logger.warning(f"Not a Team conversation (role={role}), skipping update handling")
            return False  # Not a Team conversation, skip handling

        logger.info(
            f"Handling project update for team conversation: project={project_id}, conversation={self.context.id}"
        )

        # Import the file manager for all update types
        from .project_files import ProjectFileManager

        # For ALL update types, automatically synchronize files from project storage
        # This ensures team members always have the latest files whenever any update occurs
        logger.info(f"Automatically synchronizing files after update type: {update_type}")
        sync_success = await ProjectFileManager.synchronize_files_to_team_conversation(
            context=self.context, project_id=project_id
        )
        logger.info(f"File synchronization after update: success={sync_success}")

        # Additionally handle file-specific updates for individual file operations
        if update_type in ["file_created", "file_updated", "file_deleted"]:
            # Extract filename from the message if not in data
            filename = None
            if data and "filename" in data:
                filename = data["filename"]
                logger.info(f"Got filename from data: {filename}")
            else:
                # Try to extract from message
                import re

                match = re.search(r"file: (.+?)$", message)
                if match:
                    filename = match.group(1)
                    logger.info(f"Extracted filename from message: {filename}")

            if not filename:
                logger.warning(f"Could not extract filename from update: {update_type}, {message}")
                # Return True anyway since we already did the file sync
                return sync_success

            # Check if the file exists in project storage
            file_path = ProjectFileManager.get_file_path(project_id, filename)
            if file_path.exists():
                logger.info(f"File exists in project storage: {file_path} (size: {file_path.stat().st_size} bytes)")
            else:
                logger.warning(f"File not found in project storage: {file_path}")

            # Check file metadata
            metadata = ProjectFileManager.read_file_metadata(project_id)
            if metadata and any(f.filename == filename for f in metadata.files):
                logger.info(f"File metadata found for {filename}")
            else:
                logger.warning(f"No file metadata found for {filename}")

            logger.info(f"Processing {update_type} notification for file: {filename}")

            # Process the specific file update
            success = await ProjectFileManager.process_file_update_notification(
                context=self.context, project_id=project_id, update_type=update_type, filename=filename
            )

            logger.info(f"File update notification processed: {update_type}, {filename}, success={success}")

            return success

        # For non-file updates, we've already synced the files, so return success
        logger.info(f"Update type {update_type} handled by automatic file synchronization")
        return sync_success

    async def create_information_request(
        self, title: str, description: str, priority: RequestPriority = RequestPriority.MEDIUM
    ) -> Tuple[bool, str, Optional[InformationRequest]]:
        """
        Creates an information request for assistance from the Coordinator.

        Args:
            title: Title of the request
            description: Detailed description of the request
            priority: Priority level of the request

        Returns:
            Tuple of (success, message, request)
        """
        # Check role
        role = await detect_assistant_role(self.context)
        
        if role != ConversationRole.TEAM:
            return False, "Only Team conversations can create information requests", None

        # Get project ID
        project_id = await ConversationProjectManager.get_associated_project_id(self.context)
        if not project_id:
            return False, "Conversation not associated with a project", None

        # Get user info
        participants = await self.context.get_participants()
        user_id = None
        for participant in participants.participants:
            if participant.role == "user":
                user_id = participant.id
                break

        if not user_id:
            user_id = "team-system"

        # Create request
        request = InformationRequest(
            title=title,
            description=description,
            priority=priority,
            status=RequestStatus.NEW,
            created_by=user_id,
            updated_by=user_id,
            conversation_id=str(self.context.id),
        )

        # Save request
        ProjectStorage.write_information_request(project_id, request)

        # Log the request creation
        await ProjectStorage.log_project_event(
            context=self.context,
            project_id=project_id,
            entry_type=LogEntryType.REQUEST_CREATED.value,
            message=f"Created information request: {title}",
            related_entity_id=request.request_id,
        )

        # For high priority requests, we could update project state or add an indicator
        # in the future if needed

        # Send notification
        await self.context.send_messages(
            NewConversationMessage(
                content=f"Created information request: {title}",
                message_type=MessageType.notice,
            )
        )

        return True, f"Created information request: {title}", request

    async def update_project_state(
        self, status_message: Optional[str] = None
    ) -> Tuple[bool, str, Optional[ProjectInfo]]:
        """
        Updates the project state with information from the team.

        Args:
            status_message: Optional status message or update from team

        Returns:
            Tuple of (success, message, updated_project_info)
        """
        # Check role
        role = await detect_assistant_role(self.context)
        
        if role != ConversationRole.TEAM:
            return False, "Only Team conversations can update project state", None

        # Get project ID
        project_id = await ConversationProjectManager.get_associated_project_id(self.context)
        if not project_id:
            return False, "Conversation not associated with a project", None

        # Get project info
        project_info = await ProjectManager.get_project_info(self.context)
        if not project_info:
            return False, "Project information not found", None

        # Make sure project is in the right state for team updates
        if project_info.state not in [ProjectState.READY_FOR_WORKING, ProjectState.IN_PROGRESS]:
            return (
                False,
                f"Cannot update project in {project_info.state} state. Project must be ready for team operations.",
                None,
            )

        # Get user info
        participants = await self.context.get_participants()
        user_id = None
        for participant in participants.participants:
            if participant.role == "user":
                user_id = participant.id
                break

        if not user_id:
            user_id = "team-system"

        # Update project info
        previous_state = project_info.state
        if status_message:
            project_info.status_message = status_message

        # If this is the first team update, change state to IN_PROGRESS
        if project_info.state == ProjectState.READY_FOR_WORKING:
            project_info.state = ProjectState.IN_PROGRESS

            # Log state change
            await self.log_action(
                LogEntryType.MILESTONE_PASSED,
                "Project is now in progress",
                related_entity_id=None,
                additional_metadata={
                    "previous_state": previous_state.value,
                    "new_state": ProjectState.IN_PROGRESS.value,
                },
            )

        project_info.updated_at = datetime.utcnow()

        # Save updated project info
        ProjectStorage.write_project_info(project_id, project_info)

        # Log update
        await self.log_action(
            LogEntryType.STATUS_CHANGED,
            f"Updated project status: {status_message or 'No message provided'}",
            related_entity_id=None,
            additional_metadata={
                "previous_state": previous_state.value,
                "new_state": project_info.state.value,
                "status_message": status_message,
            },
        )

        # Send notification
        await self.context.send_messages(
            NewConversationMessage(
                content=f"Updated project status: {status_message or 'No message provided'}",
                message_type=MessageType.notice,
            )
        )

        return True, f"Updated project status: {status_message or 'No message provided'}", project_info

    async def mark_criterion_completed(
        self, goal_id: str, criterion_id: str
    ) -> Tuple[bool, str, Optional[ProjectInfo]]:
        """
        Marks a success criterion as completed.

        Args:
            goal_id: ID of the goal containing the criterion
            criterion_id: ID of the criterion to mark completed

        Returns:
            Tuple of (success, message, updated_project_info)
        """
        # Check role
        role = await detect_assistant_role(self.context)
        
        if role != ConversationRole.TEAM:
            return False, "Only Team conversations can mark criteria as completed", None

        # Get project ID
        project_id = await ConversationProjectManager.get_associated_project_id(self.context)
        if not project_id:
            return False, "Conversation not associated with a project", None

        # Get briefing
        brief = await ProjectManager.get_project_brief(self.context)
        if not brief:
            return False, "Project brief not found", None

        # Find the goal and criterion
        goal = None
        criterion = None
        for g in brief.goals:
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
            user_id = "team-system"

        # Update criterion
        criterion.completed = True
        criterion.completed_at = datetime.utcnow()
        criterion.completed_by = user_id

        # Save updated brief
        brief.updated_at = datetime.utcnow()
        brief.updated_by = user_id
        brief.version += 1

        ProjectStorage.write_project_brief(project_id, brief)

        # Get project info
        project_info = await ProjectManager.get_project_info(self.context)
        if not project_info:
            return False, "Project information not found", None

        # Count completed criteria to calculate progress
        total_criteria = 0
        completed_criteria = 0
        for g in brief.goals:
            total_criteria += len(g.success_criteria)
            completed_criteria += sum(1 for c in g.success_criteria if c.completed)

        # Update project info with status message showing progress
        if total_criteria > 0:
            progress_percentage = int((completed_criteria / total_criteria) * 100)
            project_info.status_message = f"Progress: {progress_percentage}% of criteria completed ({completed_criteria}/{total_criteria})"
        
        project_info.updated_at = datetime.utcnow()
        
        # Save updated project info
        ProjectStorage.write_project_info(project_id, project_info)

        # Log completion
        await self.log_action(
            LogEntryType.CRITERION_COMPLETED,
            f"Completed criterion: {criterion.description}",
            related_entity_id=criterion_id,  # Use criterion ID directly
            additional_metadata={
                "goal_id": goal_id,
                "goal_name": goal.name,
            },
        )

        # Check if all goals are completed
        all_complete = all(all(c.completed for c in g.success_criteria) for g in brief.goals if g.success_criteria)

        if all_complete and project_info.state != ProjectState.COMPLETED:
            # Mark project as completed
            project_info.state = ProjectState.COMPLETED
            project_info.status_message = "All success criteria have been met"
            project_info.updated_at = datetime.utcnow()

            ProjectStorage.write_project_info(project_id, project_info)

            # Log project completion
            await self.log_action(
                LogEntryType.PROJECT_COMPLETED,
                "Project completed successfully",
                related_entity_id=None,  # No specific entity ID needed
            )

            # Send notification
            await self.context.send_messages(
                NewConversationMessage(
                    content="🎉 Project completed! All success criteria have been met.",
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

        return True, f"Marked criterion '{criterion.description}' as completed.", project_info

    async def report_project_completed(self, completion_summary: str) -> Tuple[bool, str, Optional[ProjectInfo]]:
        """
        Reports that the project has been completed from the team perspective.

        Args:
            completion_summary: Summary of the project completion

        Returns:
            Tuple of (success, message, updated_project_info)
        """
        # Check role
        role = await detect_assistant_role(self.context)
        
        if role != ConversationRole.TEAM:
            return False, "Only Team conversations can report project completion", None

        # Get project ID
        project_id = await ConversationProjectManager.get_associated_project_id(self.context)
        if not project_id:
            return False, "Conversation not associated with a project", None

        # Get project info
        project_info = await ProjectManager.get_project_info(self.context)
        if not project_info:
            return False, "Project information not found", None

        # Get user info
        participants = await self.context.get_participants()
        user_id = None
        for participant in participants.participants:
            if participant.role == "user":
                user_id = participant.id
                break

        if not user_id:
            user_id = "team-system"

        # Update project info
        previous_state = project_info.state
        project_info.state = ProjectState.COMPLETED
        project_info.status_message = completion_summary
        project_info.updated_at = datetime.utcnow()

        # Save updated project info
        ProjectStorage.write_project_info(project_id, project_info)

        # Log project completion
        await self.log_action(
            LogEntryType.PROJECT_COMPLETED,
            "Project marked as completed",
            related_entity_id=None,  # No specific entity ID needed
            additional_metadata={
                "previous_state": previous_state.value,
                "completion_summary": completion_summary,
            },
        )

        # Send notification
        await self.context.send_messages(
            NewConversationMessage(
                content="🎉 Project has been marked as completed.",
                message_type=MessageType.notice,
            )
        )

        return True, "Project has been marked as completed", project_info

    async def get_project_brief_info(self) -> Dict:
        """
        Gets information about the project brief.

        Returns:
            Dictionary with brief information
        """
        brief = await ProjectManager.get_project_brief(self.context)
        if not brief:
            return {
                "has_brief": False,
                "message": "No project brief found",
            }

        return {
            "has_brief": True,
            "project_name": brief.project_name,
            "project_description": brief.project_description,
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
                for goal in brief.goals
            ],
            "timeline": brief.timeline,
            "additional_context": brief.additional_context,
        }

    async def get_project_info(self) -> Dict:
        """
        Gets information about the project.

        Returns:
            Dictionary with project information
        """
        project_id = await ConversationProjectManager.get_associated_project_id(self.context)
        if not project_id:
            return {
                "has_project": False,
                "message": "This conversation is not associated with a project",
            }

        role = await detect_assistant_role(self.context)

        brief = await ProjectManager.get_project_brief(self.context)
        project_info = await ProjectManager.get_project_info(self.context)

        # Get information requests made by this conversation
        requests = await ProjectManager.get_information_requests(self.context)
        my_requests = [r for r in requests if r.conversation_id == str(self.context.id)]
        open_requests_count = len(my_requests)

        return {
            "has_project": True,
            "project_id": project_id,
            "role": role.value if role else None,
            "project_name": brief.project_name if brief else "Unnamed Project",
            "project_description": brief.project_description if brief else "",
            "status": project_info.state.value if project_info else "unknown",
            "status_message": project_info.status_message if project_info and project_info.status_message else "",
            "open_requests": open_requests_count,
            "pending_requests": [
                {
                    "id": req.request_id,
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
