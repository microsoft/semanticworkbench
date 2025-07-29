"""
Knowledge brief management operations for Knowledge Transfer Assistant.

Handles knowledge brief creation, updates, and retrieval.
"""

from typing import Optional

from semantic_workbench_assistant.assistant_app import ConversationContext

from ..data import InspectorTab, KnowledgeBrief, LogEntryType
from ..logging import logger
from ..notifications import Notifications
from ..storage import ShareStorage
from ..utils import require_current_user
from .share_manager import ShareManager


class KnowledgeBriefManager:
    """Manages knowledge brief operations."""

    @staticmethod
    async def get_knowledge_brief(context: ConversationContext) -> Optional[KnowledgeBrief]:
        share_id = await ShareManager.get_share_id(context)
        if not share_id:
            return None
        return ShareStorage.read_knowledge_brief(share_id)

    @staticmethod
    async def update_knowledge_brief(
        context: ConversationContext,
        title: str,
        description: str,
        timeline: Optional[str] = None,
    ) -> Optional[KnowledgeBrief]:
        share_id = await ShareManager.get_share_id(context)
        if not share_id:
            logger.error("Cannot update brief: no share associated with this conversation")
            return

        current_user_id = await require_current_user(context, "update brief")
        if not current_user_id:
            return

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
