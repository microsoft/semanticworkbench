"""
Project lifecycle management for Knowledge Transfer Assistant.

Handles project state updates, completion, and lifecycle operations.
"""

from datetime import datetime
from typing import List, Optional, Tuple

from semantic_workbench_assistant.assistant_app import ConversationContext

from ..data import InspectorTab, KnowledgePackage, LogEntryType
from ..logging import logger
from ..notifications import Notifications
from ..storage import ShareStorage
from ..storage_models import ConversationRole
from ..utils import require_current_user
from .share_management import ShareManagement


class ProjectLifecycleManager:
    """Manages project lifecycle and state operations."""

    @staticmethod
    async def update_share_state(
        context: ConversationContext,
        status_message: Optional[str] = None,
    ) -> Tuple[bool, Optional[KnowledgePackage]]:
        try:

            share_id = await ShareManagement.get_share_id(context)
            if not share_id:
                logger.error("Cannot update project state: no project associated with this conversation")
                return False, None

            current_user_id = await require_current_user(context, "update project state")
            if not current_user_id:
                return False, None

            project_info = ShareStorage.read_share_info(share_id)
            if not project_info:
                logger.error(f"Cannot update project state: no project info found for {share_id}")
                return False, None

            if status_message:
                project_info.transfer_notes = status_message

            project_info.updated_at = datetime.utcnow()
            ShareStorage.write_share_info(share_id, project_info)

            event_type = LogEntryType.STATUS_CHANGED
            message = "Updated status"
            if status_message:
                message += f": {status_message}"

            await ShareStorage.log_share_event(
                context=context,
                share_id=share_id,
                entry_type=event_type.value,
                message=message,
                metadata={
                    "status_message": status_message,
                },
            )

            return True, project_info

        except Exception as e:
            logger.exception(f"Error updating project state: {e}")
            return False, None

    @staticmethod
    async def update_share_info(
        context: ConversationContext,
        progress: Optional[int] = None,
        status_message: Optional[str] = None,
        next_actions: Optional[List[str]] = None,
    ) -> Optional[KnowledgePackage]:

        share_id = await ShareManagement.get_share_id(context)
        if not share_id:
            logger.error("Cannot update project info: no project associated with this conversation")
            return None

        current_user_id = await require_current_user(context, "update project info")
        if not current_user_id:
            return None

        project_info = ShareStorage.read_share_info(share_id)
        if not project_info:
            logger.error(f"Cannot update project info: no project info found for {share_id}")
            return None

        if status_message:
            project_info.transfer_notes = status_message

        if next_actions:
            project_info.next_learning_actions = next_actions

        project_info.updated_at = datetime.utcnow()
        project_info.updated_by = current_user_id

        if hasattr(project_info, "version"):
            project_info.version += 1

        ShareStorage.write_share_info(share_id, project_info)

        event_type = LogEntryType.STATUS_CHANGED
        message = "Updated status"
        if status_message:
            message += f": {status_message}"

        await ShareStorage.log_share_event(
            context=context,
            share_id=share_id,
            entry_type=event_type.value,
            message=message,
            metadata={
                "status_message": status_message,
            },
        )

        return project_info

    @staticmethod
    async def complete_project(
        context: ConversationContext,
        summary: Optional[str] = None,
    ) -> Tuple[bool, Optional[KnowledgePackage]]:
        try:

            share_id = await ShareManagement.get_share_id(context)
            if not share_id:
                logger.error("Cannot complete project: no project associated with this conversation")
                return False, None

            role = await ShareManagement.get_share_role(context)
            if role != ConversationRole.COORDINATOR:
                logger.error("Only Coordinator can complete a project")
                return False, None

            status_message = summary if summary else "KnowledgePackage completed successfully"
            success, project_info = await ProjectLifecycleManager.update_share_state(
                context=context,
                status_message=status_message,
            )

            if not success or not project_info:
                return False, None

            await ShareStorage.log_share_event(
                context=context,
                share_id=share_id,
                entry_type=LogEntryType.SHARE_COMPLETED.value,
                message=f"KnowledgePackage completed: {status_message}",
            )

            await Notifications.notify_all(context, share_id, f"🎉 **Project Completed**: {status_message}")
            await Notifications.notify_all_state_update(context, share_id, [InspectorTab.BRIEF, InspectorTab.LEARNING, InspectorTab.SHARING, InspectorTab.DEBUG])

            return True, project_info

        except Exception as e:
            logger.exception(f"Error completing project: {e}")
            return False, None