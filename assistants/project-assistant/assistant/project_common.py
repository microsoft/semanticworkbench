"""
Common utilities shared between project assistant modes.

This module provides shared functionality for team and coordinator conversation handlers,
helping to reduce code duplication and maintain consistency.
"""

import logging
from typing import Dict, Optional

from semantic_workbench_assistant.assistant_app import ConversationContext

from .project_data import LogEntryType
from .project_storage import ConversationProjectManager, ProjectStorage

logger = logging.getLogger(__name__)


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
    project_id = await ConversationProjectManager.get_associated_project_id(context)
    if not project_id:
        return

    await ProjectStorage.log_project_event(
        context=context,
        project_id=project_id,
        entry_type=entry_type.value,
        message=message,
        related_entity_id=related_entity_id,
        metadata=additional_metadata,
    )
