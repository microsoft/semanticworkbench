"""
Common utilities shared between knowledge transfer assistant modes.

This module provides shared functionality for team and coordinator conversation handlers,
helping to reduce code duplication and maintain consistency.
"""

from enum import Enum
from typing import Dict, Optional

from semantic_workbench_assistant.assistant_app import ConversationContext

from .conversation_share_link import ConversationKnowledgePackageManager
from .data import LogEntryType
from .logging import logger
from .storage import ShareStorage
from .storage_models import ConversationRole
from semantic_workbench_api_model.workbench_model import Conversation


class ConversationType(Enum):
    COORDINATOR = "coordinator"
    TEAM = "team"
    SHAREABLE_TEMPLATE = "shareable_template"


def detect_conversation_type(conversation: Conversation) -> ConversationType:
    conversation_metadata = conversation.metadata or {}
    conversation_type = ConversationType.COORDINATOR
    # Coordinator conversations will not have a share_id or
    # is_team_conversation flag in the metadata. So, if they are there, we just
    # need to decide if it's a shareable template or a team conversation.
    share_id = conversation_metadata.get("share_id")
    if conversation_metadata.get("is_team_conversation", False) and share_id:
        # If this conversation was imported from another, it indicates it's from
        # share redemption.
        if conversation.imported_from_conversation_id:
            conversation_type = ConversationType.TEAM
            # TODO: This might work better for detecting a redeemed link, but
            # hasn't been validated.

            # if conversation_metadata.get("share_redemption") and conversation_metadata.get("share_redemption").get(
            #     "conversation_share_id"
            # ):
            #     conversation_type = ConversationType.TEAM
        else:
            conversation_type = ConversationType.SHAREABLE_TEMPLATE
    return conversation_type


async def detect_assistant_role(context: ConversationContext) -> ConversationRole:
    """
    Detects whether this conversation is in Coordinator or Team mode.

    This method examines the conversation metadata to determine the role of the
    current conversation in the knowledge transfer. The role is always stored in
    the conversation metadata as "share_role".

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


async def get_shared_conversation_id(context: ConversationContext) -> Optional[str]:
    """
    Get the shared conversation ID for a coordinator conversation.

    This utility function retrieves the share ID and finds the associated
    shareable template conversation ID from the knowledge package.

    Args:
        context: The conversation context (should be a coordinator conversation)

    Returns:
        The shared conversation ID if found, None otherwise
    """
    try:
        share_id = await ConversationKnowledgePackageManager.get_associated_share_id(context)
        if not share_id:
            return None

        knowledge_package = ShareStorage.read_share(share_id)
        if not knowledge_package or not knowledge_package.shared_conversation_id:
            return None

        return knowledge_package.shared_conversation_id
    except Exception as e:
        logger.error(f"Error getting shared conversation ID: {e}")
        return None


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
