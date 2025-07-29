"""
Common utilities shared between knowledge transfer assistant modes.

This module provides shared functionality for team and coordinator conversation handlers,
helping to reduce code duplication and maintain consistency.
"""

from typing import Dict, Optional

from semantic_workbench_assistant.assistant_app import ConversationContext

from .domain.share_manager import ShareManager
from .data import LogEntryType
from .storage import ShareStorage


async def log_transfer_action(
    context: ConversationContext,
    entry_type: LogEntryType,
    message: str,
    related_entity_id: Optional[str] = None,
    additional_metadata: Optional[Dict] = None,
) -> None:
    """
    Log an action to the knowledge transfer log.

    This utility function handles retrieving the share ID and logging the event
    using the appropriate storage mechanism. It's used by both Coordinator and Team mode
    handlers to maintain consistent logging.

    Args:
        context: The conversation context
        entry_type: Type of log entry
        message: Human-readable description of the action
        related_entity_id: Optional ID of a related entity (e.g., request ID)
        additional_metadata: Optional additional metadata to include in the log
    """
    share_id = await ShareManager.get_share_id(context)
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
