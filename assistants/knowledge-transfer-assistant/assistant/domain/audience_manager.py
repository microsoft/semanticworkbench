"""
Knowledge transfer lifecycle management for Knowledge Transfer Assistant.

Handles knowledge transfer state updates, completion, and lifecycle operations.
"""

from datetime import datetime
from typing import Tuple

from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant.notifications import Notifications

from .share_manager import ShareManager

from ..data import InspectorTab, LogEntryType
from ..logging import logger
from ..storage import ShareStorage


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
            share_id = await ShareManager.get_share_id(context)
            if not share_id:
                return (
                    False,
                    "No knowledge package associated with this conversation. Please create a knowledge brief first.",
                )

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

            await Notifications.notify(context, "Audience updated.")
            await Notifications.notify_all_state_update(context, share_id, [InspectorTab.DEBUG])

            return True, f"Target audience updated successfully: {audience_description}"

        except Exception as e:
            logger.exception(f"Error updating audience: {e}")
            return False, "Failed to update the audience. Please try again."
