"""
Knowledge transfer lifecycle management for Knowledge Transfer Assistant.

Handles knowledge transfer state updates, completion, and lifecycle operations.
"""

from datetime import UTC, datetime

from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant.data import InspectorTab, LogEntryType
from assistant.notifications import Notifications

from .share_manager import ShareManager


class AudienceManager:
    @staticmethod
    async def update_audience(
        context: ConversationContext,
        audience_description: str,
    ) -> None:
        """
        Update the target audience description for a knowledge share.
        """
        share = await ShareManager.get_share(context)
        share.audience = audience_description.strip()
        share.updated_at = datetime.now(UTC)
        await ShareManager.set_share(context, share)

        await ShareManager.log_share_event(
            context=context,
            entry_type=LogEntryType.STATUS_CHANGED.value,
            message=f"Updated target audience: {audience_description}",
            metadata={
                "audience": audience_description,
            },
        )

        await Notifications.notify(context, "Audience updated.")
        await Notifications.notify_all_state_update(context, [InspectorTab.DEBUG])

    @staticmethod
    async def update_audience_takeaways(
        context: ConversationContext,
        takeaways: list[str],
    ) -> None:
        """
        Update the key takeaways for the target audience.
        """
        share = await ShareManager.get_share(context)
        share.audience_takeaways = takeaways
        share.updated_at = datetime.now(UTC)
        await ShareManager.set_share(context, share)

        await ShareManager.log_share_event(
            context=context,
            entry_type=LogEntryType.STATUS_CHANGED.value,
            message=f"Updated audience takeaways: {takeaways}",
            metadata={
                "takeaways": takeaways,
            },
        )

        await Notifications.notify(context, "Audience takeaways updated.")
        await Notifications.notify_all_state_update(context, [InspectorTab.BRIEF])
