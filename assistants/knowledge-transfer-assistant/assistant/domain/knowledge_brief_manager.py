"""
Knowledge brief management operations for Knowledge Transfer Assistant.

Handles knowledge brief creation, updates, and retrieval.
"""

from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant.data import InspectorTab, KnowledgeBrief, LogEntryType
from assistant.notifications import Notifications
from assistant.storage import ShareStorage
from assistant.utils import require_current_user

from .share_manager import ShareManager


class KnowledgeBriefManager:
    """Manages knowledge brief operations."""

    @staticmethod
    async def get_knowledge_brief(
        context: ConversationContext,
    ) -> KnowledgeBrief | None:
        share_id = await ShareManager.get_share_id(context)
        return ShareStorage.read_knowledge_brief(share_id)

    @staticmethod
    async def update_knowledge_brief(
        context: ConversationContext,
        title: str,
        description: str,
        timeline: str | None = None,
    ) -> KnowledgeBrief:
        share_id = await ShareManager.get_share_id(context)
        current_user_id = await require_current_user(context, "update brief")

        brief = KnowledgeBrief(
            title=title,
            content=description,
            timeline=timeline,
            created_by=current_user_id,
            updated_by=current_user_id,
            conversation_id=str(context.id),
        )

        ShareStorage.write_knowledge_brief(share_id, brief)

        # Check if this is a creation or an update
        existing_brief = ShareStorage.read_knowledge_brief(share_id)
        if existing_brief:
            # This is an update
            await ShareManager.log_share_event(
                context=context,
                entry_type=LogEntryType.BRIEFING_UPDATED.value,
                message=f"Updated brief: {title}",
            )
        else:
            # This is a creation
            await ShareManager.log_share_event(
                context=context,
                entry_type=LogEntryType.BRIEFING_CREATED.value,
                message=f"Created brief: {title}",
            )

        await Notifications.notify_all(context, share_id, "Knowledge brief has been updated")
        await Notifications.notify_all_state_update(context, share_id, [InspectorTab.BRIEF])

        return brief
