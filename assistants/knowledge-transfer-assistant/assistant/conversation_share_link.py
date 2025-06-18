"""
Manages associations between conversations and projects.

This module handles the linking of conversations to projects,
defining roles (Coordinator/Team) and maintaining relationships.
"""

from typing import List, Optional

from pydantic import BaseModel
from semantic_workbench_assistant.assistant_app import ConversationContext
from semantic_workbench_assistant.storage import read_model, write_model

from .logging import logger
from .storage import ShareStorageManager
from .storage_models import ConversationRole


class ConversationKnowledgePackageManager:
    """Manages the association between conversations and projects."""

    class ConversationRoleInfo(BaseModel):
        """Stores a conversation's role in a project."""

        share_id: str
        role: ConversationRole
        conversation_id: str

    class ProjectAssociation(BaseModel):
        """Stores a conversation's project association."""

        share_id: str

    @staticmethod
    async def get_linked_conversations(context: ConversationContext) -> List[str]:
        """
        Gets all conversations linked to this one through the same project.
        """
        try:
            # Get project ID
            share_id = await ConversationKnowledgePackageManager.get_associated_share_id(context)
            if not share_id:
                return []

            # Get the linked conversations directory
            linked_dir = ShareStorageManager.get_linked_conversations_dir(share_id)
            if not linked_dir.exists():
                return []

            # Get all conversation files in the directory
            result = []
            conversation_id = str(context.id)

            # Each file in the directory represents a linked conversation
            # The filename itself is the conversation ID
            for file_path in linked_dir.glob("*"):
                if file_path.is_file():
                    # The filename is the conversation ID
                    conv_id = file_path.name
                    if conv_id != conversation_id:
                        result.append(conv_id)

            return result

        except Exception as e:
            logger.error(f"Error getting linked conversations: {e}")
            return []

    @staticmethod
    async def set_conversation_role(context: ConversationContext, share_id: str, role: ConversationRole) -> None:
        """
        Sets the role of a conversation in a project.
        """
        role_data = ConversationKnowledgePackageManager.ConversationRoleInfo(
            share_id=share_id, role=role, conversation_id=str(context.id)
        )
        role_path = ShareStorageManager.get_conversation_role_file_path(context)
        write_model(role_path, role_data)

    @staticmethod
    async def get_conversation_role(context: ConversationContext) -> Optional[ConversationRole]:
        """
        Gets the role of a conversation in a project.
        """
        role_path = ShareStorageManager.get_conversation_role_file_path(context)
        role_data = read_model(role_path, ConversationKnowledgePackageManager.ConversationRoleInfo)

        if role_data:
            return role_data.role

        return None

    @staticmethod
    async def associate_conversation_with_share(context: ConversationContext, share_id: str) -> None:
        """
        Associates a conversation with a project.
        """
        logger.debug(f"Associating conversation {context.id} with project {share_id}")

        try:
            # 1. Store the project association in the conversation's storage directory
            project_data = ConversationKnowledgePackageManager.ProjectAssociation(share_id=share_id)
            project_path = ShareStorageManager.get_conversation_share_file_path(context)
            logger.debug(f"Writing project association to {project_path}")
            write_model(project_path, project_data)

            # 2. Register this conversation in the project's linked_conversations directory
            linked_dir = ShareStorageManager.get_linked_conversations_dir(share_id)
            logger.debug(f"Registering in linked_conversations directory: {linked_dir}")
            conversation_file = linked_dir / str(context.id)

            # Touch the file to create it if it doesn't exist
            # We don't need to write any content to it, just its existence is sufficient
            conversation_file.touch(exist_ok=True)
            logger.debug(f"Created conversation link file: {conversation_file}")
        except Exception as e:
            logger.error(f"Error associating conversation with project: {e}")
            raise

    @staticmethod
    async def get_associated_share_id(context: ConversationContext) -> Optional[str]:
        """
        Gets the project ID associated with a conversation.
        """
        project_path = ShareStorageManager.get_conversation_share_file_path(context)
        project_data = read_model(project_path, ConversationKnowledgePackageManager.ProjectAssociation)

        if project_data:
            return project_data.share_id

        return None
