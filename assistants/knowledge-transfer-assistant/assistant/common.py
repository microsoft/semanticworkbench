"""
Common utilities shared between project assistant modes.

This module provides shared functionality for team and coordinator conversation handlers,
helping to reduce code duplication and maintain consistency.
"""

from typing import Dict, Optional

from semantic_workbench_assistant.assistant_app import ConversationContext

from .conversation_share_link import ConversationKnowledgePackageManager
from .data import LogEntryType
from .logging import logger
from .storage import ShareStorage
from .storage_models import ConversationRole


async def detect_assistant_role(context: ConversationContext) -> ConversationRole:
    """
    Detects whether this conversation is in Coordinator or Team mode.

    This method examines the conversation metadata to determine the role
    of the current conversation in the project. The role is always stored
    in the conversation metadata as "share_role".

    Args:
        context: The conversation context to examine

    Returns:
        ConversationRole.COORDINATOR or ConversationRole.TEAM
    """
    try:
        conversation = await context.get_conversation()
        metadata = conversation.metadata or {}
        role_str = metadata.get("project_role", "coordinator")

        if role_str == "team":
            return ConversationRole.TEAM
        else:
            return ConversationRole.COORDINATOR
    except Exception as e:
        logger.exception(f"Error detecting assistant role: {e}")
        # Default to coordinator role if we can't determine
        return ConversationRole.COORDINATOR


async def log_project_action(
    context: ConversationContext,
    entry_type: LogEntryType,
    message: str,
    related_entity_id: Optional[str] = None,
    additional_metadata: Optional[Dict] = None,
) -> None:
    """
    Log an action to the project log.

    This utility function handles retrieving the project ID and logging the event
    using the appropriate storage mechanism. It's used by both Coordinator and Team mode
    handlers to maintain consistent logging.

    Args:
        context: The conversation context
        entry_type: Type of log entry
        message: Human-readable description of the action
        related_entity_id: Optional ID of a related entity (e.g., request ID)
        additional_metadata: Optional additional metadata to include in the log
    """
    share_id = await ConversationKnowledgePackageManager.get_associated_share_id(context)
    if not share_id:
        return

    await ShareStorage.log_share_event(
        context=context,
        share_id=share_id,
        entry_type=entry_type.value,
        message=message,
        related_entity_id=related_entity_id,
        metadata=additional_metadata,
    )
