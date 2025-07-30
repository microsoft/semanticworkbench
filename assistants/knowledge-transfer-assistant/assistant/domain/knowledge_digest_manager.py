"""
Knowledge digest management for Knowledge Transfer Assistant.

Handles knowledge digest operations including auto-updating from conversations.
"""

import re
from datetime import UTC, datetime

import openai_client
from semantic_workbench_api_model.workbench_model import ParticipantRole
from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant.config import assistant_config
from assistant.data import InspectorTab, KnowledgeDigest, LogEntryType
from assistant.notifications import Notifications
from assistant.storage import ShareStorage
from assistant.utils import require_current_user

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
        if not share_id:
            raise ValueError("Cannot update knowledge digest: no share associated with this conversation")

        current_user_id = await require_current_user(context, "update knowledge digest")
        if not current_user_id:
            raise ValueError("Could not identify current user")

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
            share_id,
            [InspectorTab.BRIEF],
        )

        return digest

    @staticmethod
    async def auto_update_knowledge_digest(
        context: ConversationContext,
    ) -> KnowledgeDigest:
        """
        Automatically updates the knowledge digest by analyzing chat history.
        """
        messages = await context.get_messages()
        chat_history = messages.messages

        share_id = await ShareManager.get_share_id(context)
        if not share_id:
            raise ValueError("Cannot auto-update knowledge digest: no share associated with this conversation")

        current_user_id = await require_current_user(context, "auto-update knowledge digest")
        if not current_user_id:
            raise ValueError("Could not identify current user")

        # Skip if no messages to analyze
        if not chat_history:
            raise ValueError("No chat history to analyze for knowledge digest update")

        # Format the chat history for the prompt
        chat_history_text = ""
        for msg in chat_history:
            sender_type = "User" if msg.sender and msg.sender.participant_role == ParticipantRole.user else "Assistant"
            chat_history_text += f"{sender_type}: {msg.content}\n\n"

        # Construct the knowledge digest prompt with the chat history
        config = await assistant_config.get(context.assistant)
        digest_prompt = f"""
        {config.prompt_config.knowledge_digest_prompt}

        <CHAT_HISTORY>
        {chat_history_text}
        </CHAT_HISTORY>
        """

        async with openai_client.create_client(config.service_config, api_version="2024-06-01") as client:
            completion = await client.chat.completions.create(
                model=config.request_config.openai_model,
                messages=[{"role": "user", "content": digest_prompt}],
                max_tokens=config.coordinator_config.max_digest_tokens,
            )

            content = completion.choices[0].message.content or ""
            digest_content = ""
            match = re.search(r"<KNOWLEDGE_DIGEST>(.*?)</KNOWLEDGE_DIGEST>", content, re.DOTALL)
            digest_content = match.group(1).strip() if match else content.strip()

        if not digest_content:
            raise ValueError("No content extracted from knowledge digest LLM analysis")

        return await KnowledgeDigestManager.update_knowledge_digest(
            context=context,
            content=digest_content,
            is_auto_generated=True,
        )
