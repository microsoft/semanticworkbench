"""
Manages associations between conversations in a knowledge transfer.

This module handles the linking of conversations to knowledge transfer shares,
defining roles (Coordinator/Team) and maintaining relationships.
"""

from typing import List, Optional

from pydantic import BaseModel
from semantic_workbench_assistant.assistant_app import ConversationContext
from semantic_workbench_assistant.storage import read_model, write_model

from .data import TeamConversationInfo
from .logging import logger
from .storage import ShareStorageManager
from .storage_models import ConversationRole
from .utils import get_current_user


class ConversationKnowledgePackageManager:
    """Manages the association between conversations and knowledge transfers."""

    class ConversationRoleInfo(BaseModel):
        """Stores a conversation's role in a knowledge transfer share."""

        share_id: str
        role: ConversationRole
        conversation_id: str

    class ShareAssociation(BaseModel):
        """Stores a conversation's share association."""

        share_id: str

    @staticmethod
    async def get_linked_conversations(context: ConversationContext) -> List[str]:
        """
        Gets all conversations linked to this one through the same knowledge transfer share.
        """
        try:
            share_id = await ConversationKnowledgePackageManager.get_associated_share_id(context)
            if not share_id:
                return []

            # Load the knowledge package
            from .storage import ShareStorage

            knowledge_package = ShareStorage.read_share(share_id)
            if not knowledge_package:
                return []

            # Get all linked conversations, excluding current conversation
            conversation_id = str(context.id)
            return knowledge_package.get_all_linked_conversations(exclude_current=conversation_id)

        except Exception as e:
            logger.error(f"Error getting linked conversations: {e}")
            return []

    @staticmethod
    async def set_conversation_role(context: ConversationContext, share_id: str, role: ConversationRole) -> None:
        """
        Sets the role of a conversation in a knowledge transfer share.
        """
        role_data = ConversationKnowledgePackageManager.ConversationRoleInfo(
            share_id=share_id, role=role, conversation_id=str(context.id)
        )
        role_path = ShareStorageManager.get_conversation_role_file_path(context)
        write_model(role_path, role_data)

    @staticmethod
    async def get_conversation_role(context: ConversationContext) -> Optional[ConversationRole]:
        """
        Gets the role of a conversation in a knowledge transfer.
        """
        role_path = ShareStorageManager.get_conversation_role_file_path(context)
        role_data = read_model(role_path, ConversationKnowledgePackageManager.ConversationRoleInfo)

        if role_data:
            return role_data.role

        return None

    @staticmethod
    async def associate_conversation_with_share(context: ConversationContext, share_id: str) -> None:
        """
        Associates a conversation with a knowledge share and captures redeemer information.
        """
        logger.debug(f"Associating conversation {context.id} with share {share_id}")

        try:
            # 1. Store the share association in the conversation's storage directory
            share_data = ConversationKnowledgePackageManager.ShareAssociation(share_id=share_id)
            share_path = ShareStorageManager.get_conversation_share_file_path(context)
            logger.debug(f"Writing share association to {share_path}")
            write_model(share_path, share_data)

            # 2. Capture redeemer information and store in knowledge package
            # This method will now handle storing the conversation in JSON instead of file system
            await ConversationKnowledgePackageManager._capture_redeemer_info(context, share_id)

        except Exception as e:
            logger.error(f"Error associating conversation with share: {e}")
            raise

    @staticmethod
    async def _capture_redeemer_info(context: ConversationContext, share_id: str) -> None:
        """
        Captures the redeemer (first non-assistant participant) information and stores it in the knowledge package.
        Only captures info for actual team member conversations, not coordinator or shared conversations.
        """
        try:
            # Load the knowledge package
            from .storage import ShareStorage

            knowledge_package = ShareStorage.read_share(share_id)
            if not knowledge_package:
                logger.warning(f"Could not load knowledge package {share_id} to capture redeemer info")
                return

            conversation_id = str(context.id)

            # Skip if this is the coordinator conversation
            if conversation_id == knowledge_package.coordinator_conversation_id:
                logger.debug(f"Skipping redeemer capture for coordinator conversation {conversation_id}")
                return

            # Skip if this is the shared conversation template
            if conversation_id == knowledge_package.shared_conversation_id:
                logger.debug(f"Skipping redeemer capture for shared conversation template {conversation_id}")
                return

            # If we get here, it's a team member conversation - capture redeemer info
            # Get current user information (the redeemer)
            user_id, user_name = await get_current_user(context)

            if not user_id or not user_name:
                logger.warning(f"Could not identify redeemer for conversation {conversation_id}")
                return

            # Create team conversation info
            team_conversation_info = TeamConversationInfo(
                conversation_id=conversation_id, redeemer_user_id=user_id, redeemer_name=user_name
            )

            # Add to knowledge package
            knowledge_package.team_conversations[conversation_id] = team_conversation_info

            # Save the updated knowledge package
            ShareStorage.write_share(share_id, knowledge_package)
            logger.debug(f"Captured redeemer info for team conversation {conversation_id}: {user_name} ({user_id})")

        except Exception as e:
            logger.error(f"Error capturing redeemer info: {e}")
            # Don't re-raise - this is not critical for the association process

    @staticmethod
    async def get_associated_share_id(context: ConversationContext) -> Optional[str]:
        """
        Gets the share ID associated with a conversation.
        """
        share_path = ShareStorageManager.get_conversation_share_file_path(context)
        share_data = read_model(share_path, ConversationKnowledgePackageManager.ShareAssociation)

        if share_data:
            return share_data.share_id

        return None
