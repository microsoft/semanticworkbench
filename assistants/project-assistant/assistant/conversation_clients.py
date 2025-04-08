"""
Project assistant functionality for cross-conversation communication.

This module handles the project assistant's core functionality for managing
communication between conversations. It provides utilities for creating temporary
contexts and accessing other conversations.
"""

import logging
from typing import Any, Optional, Tuple

import semantic_workbench_api_model.workbench_service_client as wsc
from pydantic import BaseModel
from semantic_workbench_api_model.workbench_service_client import ConversationAPIClient
from semantic_workbench_assistant import settings
from semantic_workbench_assistant.assistant_app import ConversationContext
from semantic_workbench_assistant.storage import read_model

from .project_storage import ConversationProjectManager, ProjectRole, ProjectStorageManager


# Define models for project role data
class ProjectRoleData(BaseModel):
    """Data model for storing a conversation's role in a project."""

    conversation_id: str
    role: ProjectRole


logger = logging.getLogger(__name__)


class ConversationClientManager:
    """
    Manages API clients for accessing other conversations.

    This utility class provides methods for creating API clients and temporary contexts
    that can be used to interact with other conversations in the same project.
    """

    @staticmethod
    def get_conversation_client(context: ConversationContext, conversation_id: str) -> ConversationAPIClient:
        """
        Gets a client for accessing another conversation.

        Args:
            context: Source conversation context
            conversation_id: ID of the target conversation

        Returns:
            A client for the target conversation
        """
        # Create a client for the target conversation
        builder = wsc.WorkbenchServiceClientBuilder(
            base_url=str(settings.workbench_service_url),
            assistant_service_id=context.assistant._assistant_service_id,
            api_key=settings.workbench_service_api_key,
        )
        client = builder.for_conversation(
            assistant_id=context.assistant.id,
            conversation_id=conversation_id,
        )
        return client

    @staticmethod
    async def get_coordinator_client_for_project(
        context: ConversationContext, project_id: str
    ) -> Tuple[Optional[Any], Optional[str]]:
        """
        Gets a client for accessing the Coordinator conversation for a project.

        Args:
            context: Source conversation context
            project_id: ID of the project

        Returns:
            Tuple of (client, coordinator_conversation_id) or (None, None) if not found
        """
        # Look for the Coordinator conversation directory
        coordinator_dir = ProjectStorageManager.get_project_dir(project_id) / ProjectRole.COORDINATOR.value
        if not coordinator_dir.exists():
            return None, None

        # Find the role file that contains the conversation ID
        role_file = coordinator_dir / "conversation_role.json"
        if not role_file.exists():
            role_file = coordinator_dir / "project_role.json"
            if not role_file.exists():
                return None, None

        # Read the role information to get the Coordinator conversation ID
        role_data = read_model(role_file, ConversationProjectManager.ConversationRoleInfo)
        if not role_data or not role_data.conversation_id:
            return None, None

        # Get the Coordinator conversation ID
        coordinator_conversation_id = role_data.conversation_id

        # Don't create a client if the Coordinator is the current conversation
        if coordinator_conversation_id == str(context.id):
            return None, coordinator_conversation_id

        # Create a client for the Coordinator conversation
        client = ConversationClientManager.get_conversation_client(context, coordinator_conversation_id)
        return client, coordinator_conversation_id
        
    @staticmethod
    async def create_temporary_context_for_conversation(
        source_context: ConversationContext, target_conversation_id: str
    ) -> Optional[ConversationContext]:
        """
        Creates a temporary context for the target conversation ID.

        Args:
            source_context: The current conversation context to derive settings from
            target_conversation_id: The ID of the target conversation to create a context for

        Returns:
            A temporary conversation context for the target conversation, or None if creation failed
        """
        try:
            # Get client for the target conversation
            target_client = ConversationClientManager.get_conversation_client(source_context, target_conversation_id)

            # To create a temporary context, we need:
            # 1. The conversation details
            # 2. The assistant details
            conversation = await target_client.get_conversation()
            if not conversation:
                return None

            # We'll use the same assistant as in the source context
            assistant = source_context.assistant

            # Create a temporary context with the same properties as the original
            # but pointing to a different conversation
            from semantic_workbench_assistant.assistant_app.context import ConversationContext

            temp_context = ConversationContext(
                assistant=assistant,
                id=target_conversation_id,
                title=source_context.title,
            )

            return temp_context

        except Exception as e:
            logger.error(f"Error creating temporary context: {e}")
            return None


