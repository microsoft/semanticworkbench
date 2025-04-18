"""
Common utilities shared between project assistant modes.

This module provides shared functionality for team and coordinator conversation handlers,
helping to reduce code duplication and maintain consistency.
"""

import logging
from enum import Enum
from typing import Any, Dict, Optional

from semantic_workbench_assistant.assistant_app import ConversationContext

from .project_data import LogEntryType
from .project_storage import ConversationProjectManager, ProjectStorage

logger = logging.getLogger(__name__)


class ConversationRole(str, Enum):
    """
    Enumeration of conversation roles in a project.
    
    This enum represents the role that a conversation plays in a project,
    either as a Coordinator (managing the project) or as a Team member
    (participating in the project).
    """
    COORDINATOR = "coordinator"
    TEAM = "team"


async def detect_assistant_role(context: ConversationContext) -> ConversationRole:
    """
    Detects whether this conversation is in Coordinator or Team mode.
    
    This method examines the conversation metadata to determine the role
    of the current conversation in the project. The role is always stored
    in the conversation metadata as "project_role".
    
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


async def handle_project_update(
    context: ConversationContext,
    update_type: str,
    message: str,
    data: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Process a project update notification based on the current role.

    This utility function determines the current role and routes the update
    to the appropriate handler (Coordinator or Team).

    Args:
        context: The conversation context
        update_type: Type of update (e.g., 'file_created', 'file_updated', etc.)
        message: Human-readable notification message
        data: Optional additional data about the update

    Returns:
        True if the update was handled, False otherwise
    """
    # Get the current role using metadata
    role = await detect_assistant_role(context)

    # Handle based on role
    if role == ConversationRole.COORDINATOR:
        # Import coordinator handler
        from .coordinator_mode import CoordinatorConversationHandler

        # Create handler and process update
        handler = CoordinatorConversationHandler(context)
        return await handler.handle_project_update(update_type, message, data)

    elif role == ConversationRole.TEAM:
        # Import team handler
        from .team_mode import TeamConversationHandler

        # Create handler and process update
        handler = TeamConversationHandler(context)
        return await handler.handle_project_update(update_type, message, data)

    return False  # Unknown role
