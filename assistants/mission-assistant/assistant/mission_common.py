"""
Common utilities shared between mission assistant modes.

This module provides shared functionality for field and HQ conversation handlers,
helping to reduce code duplication and maintain consistency.
"""

import logging
from typing import Dict, Optional

from semantic_workbench_assistant.assistant_app import ConversationContext

from .mission_data import LogEntryType
from .mission_storage import ConversationMissionManager, MissionStorage

logger = logging.getLogger(__name__)


async def log_mission_action(
    context: ConversationContext,
    entry_type: LogEntryType,
    message: str,
    related_entity_id: Optional[str] = None,
    additional_metadata: Optional[Dict] = None,
) -> None:
    """
    Log an action to the mission log.

    This utility function handles retrieving the mission ID and logging the event
    using the appropriate storage mechanism. It's used by both HQ and Field mode
    handlers to maintain consistent logging.

    Args:
        context: The conversation context
        entry_type: Type of log entry
        message: Human-readable description of the action
        related_entity_id: Optional ID of a related entity (e.g., request ID)
        additional_metadata: Optional additional metadata to include in the log
    """
    mission_id = await ConversationMissionManager.get_associated_mission_id(context)
    if not mission_id:
        return

    await MissionStorage.log_mission_event(
        context=context,
        mission_id=mission_id,
        entry_type=entry_type.value,
        message=message,
        related_entity_id=related_entity_id,
        metadata=additional_metadata,
    )
