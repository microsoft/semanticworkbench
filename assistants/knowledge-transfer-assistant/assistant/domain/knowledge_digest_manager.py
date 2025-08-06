from datetime import UTC, datetime

from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant.data import InspectorTab, KnowledgeDigest, LogEntryType
from assistant.notifications import Notifications
from assistant.storage import ShareStorage
from assistant.utils import get_current_user_id

from .share_manager import ShareManager


class KnowledgeDigestManager:
    """Manages knowledge digest operations."""

    @staticmethod
    async def get_knowledge_digest(
        context: ConversationContext,
    ) -> KnowledgeDigest | None:
        share_id = await ShareManager.get_share_id(context)
        if not share_id:
            return None
        return ShareStorage.read_knowledge_digest(share_id)

    @staticmethod
    async def update_knowledge_digest(
        context: ConversationContext,
        content: str,
        is_auto_generated: bool = True,
    ) -> KnowledgeDigest:
        share_id = await ShareManager.get_share_id(context)
        current_user_id = await get_current_user_id(context)

        digest = ShareStorage.read_knowledge_digest(share_id)
        is_new = False

        if not digest:
            digest = KnowledgeDigest(
                created_by=current_user_id,
                updated_by=current_user_id,
                conversation_id=str(context.id),
                content="",
            )
            is_new = True

        digest.content = content
        digest.is_auto_generated = is_auto_generated
        digest.updated_at = datetime.now(UTC)
        digest.updated_by = current_user_id
        digest.version += 1
        ShareStorage.write_knowledge_digest(share_id, digest)

        # Log the update
        event_type = LogEntryType.KNOWLEDGE_DIGEST_UPDATE
        update_type = "auto-generated" if is_auto_generated else "manual"
        message = f"{'Created' if is_new else 'Updated'} knowledge digest ({update_type})"

        await ShareManager.log_share_event(
            context=context,
            entry_type=event_type.value,
            message=message,
        )

        await Notifications.notify_all_state_update(
            context,
            [InspectorTab.BRIEF],
        )

        return digest
