"""
Knowledge transfer lifecycle management for Knowledge Transfer Assistant.

Handles knowledge transfer state updates, completion, and lifecycle operations.
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


class TransferLifecycleManager:
    """Manages knowledge transfer lifecycle and state operations."""

    @staticmethod
    async def update_share_state(
        context: ConversationContext,
        status_message: Optional[str] = None,
    ) -> Tuple[bool, Optional[KnowledgePackage]]:
        try:

            share_id = await ShareManagement.get_share_id(context)
            if not share_id:
                logger.error("Cannot update share state: no share associated with this conversation")
                return False, None

            current_user_id = await require_current_user(context, "update share state")
            if not current_user_id:
                return False, None

            share_info = ShareStorage.read_share_info(share_id)
            if not share_info:
                logger.error(f"Cannot update share state: no share info found for {share_id}")
                return False, None

            if status_message:
                share_info.transfer_notes = status_message

            share_info.updated_at = datetime.utcnow()
            ShareStorage.write_share_info(share_id, share_info)

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

            return True, share_info

        except Exception as e:
            logger.exception(f"Error updating share state: {e}")
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
            logger.error("Cannot update share info: no share associated with this conversation")
            return None

        current_user_id = await require_current_user(context, "update share info")
        if not current_user_id:
            return None

        share_info = ShareStorage.read_share_info(share_id)
        if not share_info:
            logger.error(f"Cannot update share info: no share info found for {share_id}")
            return None

        if status_message:
            share_info.transfer_notes = status_message

        if next_actions:
            share_info.next_learning_actions = next_actions

        share_info.updated_at = datetime.utcnow()
        share_info.updated_by = current_user_id

        if hasattr(share_info, "version"):
            share_info.version += 1

        ShareStorage.write_share_info(share_id, share_info)

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

        return share_info

    @staticmethod
    async def complete_transfer(
        context: ConversationContext,
        summary: Optional[str] = None,
    ) -> Tuple[bool, Optional[KnowledgePackage]]:
        try:

            share_id = await ShareManagement.get_share_id(context)
            if not share_id:
                logger.error("Cannot complete transfer: no share associated with this conversation")
                return False, None

            role = await ShareManagement.get_share_role(context)
            if role != ConversationRole.COORDINATOR:
                logger.error("Only Coordinator can complete a transfer")
                return False, None

            status_message = summary if summary else "KnowledgePackage completed successfully"
            success, share_info = await TransferLifecycleManager.update_share_state(
                context=context,
                status_message=status_message,
            )

            if not success or not share_info:
                return False, None

            await ShareStorage.log_share_event(
                context=context,
                share_id=share_id,
                entry_type=LogEntryType.SHARE_COMPLETED.value,
                message=f"KnowledgePackage completed: {status_message}",
            )

            await Notifications.notify_all(context, share_id, f"🎉 **knowledge Transfer Completed**: {status_message}")
            await Notifications.notify_all_state_update(context, share_id, [InspectorTab.BRIEF, InspectorTab.LEARNING, InspectorTab.SHARING, InspectorTab.DEBUG])

            return True, share_info

        except Exception as e:
            logger.exception(f"Error completing knowledge transfer: {e}")
            return False, None

    @staticmethod
    async def update_audience(
        context: ConversationContext,
        audience_description: str,
    ) -> Tuple[bool, str]:
        """
        Update the target audience description for a knowledge package.

        Args:
            context: Current conversation context
            audience_description: Description of the intended audience and their existing knowledge level

        Returns:
            Tuple of (success, message) where:
            - success: Boolean indicating if the update was successful
            - message: Result message
        """
        try:
            share_id = await ShareManagement.get_share_id(context)
            if not share_id:
                return False, "No knowledge package associated with this conversation. Please create a knowledge brief first."

            # Get existing knowledge package
            package = ShareStorage.read_share(share_id)
            if not package:
                return False, "No knowledge package found. Please create a knowledge brief first."

            # Update the audience
            package.audience = audience_description.strip()
            package.updated_at = datetime.utcnow()

            # Save the updated package
            ShareStorage.write_share(share_id, package)

            # Log the event
            await ShareStorage.log_share_event(
                context=context,
                share_id=share_id,
                entry_type=LogEntryType.STATUS_CHANGED.value,
                message=f"Updated target audience: {audience_description}",
                metadata={
                    "audience": audience_description,
                },
            )

            return True, f"Target audience updated successfully: {audience_description}"

        except Exception as e:
            logger.exception(f"Error updating audience: {e}")
            return False, "Failed to update the audience. Please try again."