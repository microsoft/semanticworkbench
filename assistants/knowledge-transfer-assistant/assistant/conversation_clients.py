"""
Project assistant functionality for cross-conversation communication.

This module handles the knowledge transfer assistant's core functionality for managing
communication between conversations. It provides utilities for creating temporary
contexts and accessing other conversations.
"""

from typing import Any, Optional, Tuple

from semantic_workbench_api_model.workbench_service_client import ConversationAPIClient
from semantic_workbench_assistant.assistant_app import ConversationContext
from semantic_workbench_assistant.storage import read_model

from .data import ConversationRole, ConversationShareInfo
from .logging import logger
from .storage import ShareStorageManager


class ConversationClientManager:
    """
    Manages API clients for accessing other conversations.

    This utility class provides methods for creating API clients and temporary contexts
    that can be used to interact with other conversations in the same knowledge transfer.
    """

    @staticmethod
    def get_conversation_client(
        context: ConversationContext, conversation_id: str
    ) -> ConversationAPIClient:
        """
        Gets a client for accessing another conversation.
        """
        return context.for_conversation(conversation_id)._conversation_client

    @staticmethod
    async def get_coordinator_client_for_share(
        context: ConversationContext, share_id: str
    ) -> Tuple[Optional[Any], Optional[str]]:
        """
        Gets a client for accessing the Coordinator conversation for a knowledge transfer.
        """
        # Look for the Coordinator conversation directory
        coordinator_dir = (
            ShareStorageManager.get_share_dir(share_id) / ConversationRole.COORDINATOR
        )
        if not coordinator_dir.exists():
            return None, None

        # Find the role file that contains the conversation ID
        role_file = coordinator_dir / "conversation_role.json"
        if not role_file.exists():
            role_file = coordinator_dir / "project_role.json"
            if not role_file.exists():
                return None, None

        # Read the role information to get the Coordinator conversation ID
        role_data = read_model(role_file, ConversationShareInfo)
        if not role_data or not role_data.conversation_id:
            return None, None

        # Get the Coordinator conversation ID
        coordinator_conversation_id = role_data.conversation_id

        # Don't create a client if the Coordinator is the current conversation
        if coordinator_conversation_id == str(context.id):
            return None, coordinator_conversation_id

        # Create a client for the Coordinator conversation
        client = ConversationClientManager.get_conversation_client(
            context, coordinator_conversation_id
        )
        return client, coordinator_conversation_id

    @staticmethod
    async def create_temporary_context_for_conversation(
        source_context: ConversationContext, target_conversation_id: str
    ) -> Optional[ConversationContext]:
        """
        Creates a temporary context for the target conversation ID.
        """
        try:
            # Create a temporary context with the same properties as the original
            # but pointing to a different conversation

            temp_context = source_context.for_conversation(target_conversation_id)

            return temp_context

        except Exception as e:
            logger.error(f"Error creating temporary context: {e}")
            return None
