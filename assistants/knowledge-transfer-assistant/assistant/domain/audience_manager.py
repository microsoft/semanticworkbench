"""
Knowledge transfer lifecycle management for Knowledge Transfer Assistant.

Handles knowledge transfer state updates, completion, and lifecycle operations.
"""

from datetime import datetime
from typing import Tuple

from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant.data import InspectorTab, LogEntryType
from assistant.logging import logger
from assistant.notifications import Notifications

from .share_manager import ShareManager


class AudienceManager:
    """Manages knowledge transfer lifecycle and state operations."""

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
            # Get existing knowledge package
            share = await ShareManager.get_share(context)
            if not share:
                return (
                    False,
                    "No knowledge package found. Please create a knowledge brief first.",
                )

            # Update the audience
            share.audience = audience_description.strip()
            share.updated_at = datetime.utcnow()

            # Save the updated package
            await ShareManager.set_share(context, share)

            # Log the event
            await ShareManager.log_share_event(
                context=context,
                entry_type=LogEntryType.STATUS_CHANGED.value,
                message=f"Updated target audience: {audience_description}",
                metadata={
                    "audience": audience_description,
                },
            )

            await Notifications.notify(context, "Audience updated.")
            await Notifications.notify_all_state_update(context, share.share_id, [InspectorTab.DEBUG])

            return True, f"Target audience updated successfully: {audience_description}"

        except Exception as e:
            logger.exception(f"Error updating audience: {e}")
            return False, "Failed to update the audience. Please try again."
