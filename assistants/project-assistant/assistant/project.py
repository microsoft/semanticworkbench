"""
Project assistant functionality for cross-conversation communication.

This module handles the project assistant's core functionality for managing
communication between conversations, file synchronization, and invitation management.
It implements a clean entity-based approach without backward compatibility concerns.
"""

import logging
import pathlib
from typing import Any, List, Optional, Tuple

import semantic_workbench_api_model.workbench_service_client as wsc
from pydantic import BaseModel, Field
from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_api_model.workbench_service_client import ConversationAPIClient
from semantic_workbench_assistant import settings
from semantic_workbench_assistant.assistant_app import ConversationContext
from semantic_workbench_assistant.assistant_app.context import storage_directory_for_context
from semantic_workbench_assistant.storage import read_model

from .project_data import LogEntryType
from .project_manager import ProjectManager
from .project_storage import ConversationProjectManager, ProjectRole, ProjectStorageManager
from .utils import get_current_user


# Define models for project role data
class ProjectRoleData(BaseModel):
    """Data model for storing a conversation's role in a project."""

    conversation_id: str
    role: ProjectRole


logger = logging.getLogger(__name__)


class ConversationClientManager:
    """
    Manages API clients for accessing other conversations.

    This utility class provides methods for creating API clients that can be used
    to send messages to other conversations in the same project.
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
        from semantic_workbench_assistant.storage import read_model

        from .project_storage import ConversationProjectManager, ProjectRole, ProjectStorageManager

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


class ProjectInvitation:
    """
    Manages project joining.

    Simplified version that uses project IDs directly as invitation codes.
    """

    # Keeping the minimal models needed for backward compatibility
    class Invitation(BaseModel):
        """Legacy model for a project invitation - kept for backward compatibility."""

        invitation_id: str
        project_id: str

    class InvitationsCollection(BaseModel):
        """Legacy model - kept for backward compatibility."""

        invitations: List[Any] = Field(default_factory=list)

    @staticmethod
    def _get_invitations_path(context: ConversationContext) -> pathlib.Path:
        """Legacy method kept for backward compatibility."""
        storage_dir = storage_directory_for_context(context)
        storage_dir.mkdir(parents=True, exist_ok=True)
        return storage_dir / "project_invitations.json"

    @staticmethod
    async def redeem_invitation(context: ConversationContext, project_id: str) -> Tuple[bool, str]:
        """
        Joins a project using its project ID.

        This simplified method treats the project ID directly as the invitation code,
        eliminating the need for complex invitation generation and validation.

        Args:
            context: The conversation context
            project_id: The project ID to join

        Returns:
            (success, message) tuple
        """
        try:
            # Check if project exists
            if not ProjectStorageManager.project_exists(project_id):
                return False, f"Project with ID '{project_id}' not found. Please check the ID and try again."

            # Get current user information
            current_user_id, current_username = await get_current_user(context)
            current_username = current_username or "Unknown User"

            # Join the project as a team member
            success = await ProjectManager.join_project(context, project_id, ProjectRole.TEAM)

            if not success:
                logger.error(f"Failed to join project {project_id}")
                return False, "Failed to join the project. Please try again."

            # Log the join in the project log
            await ProjectManager.add_log_entry(
                context=context,
                entry_type=LogEntryType.PARTICIPANT_JOINED,
                message="Joined project as team member",
                metadata={
                    "project_id": project_id,
                },
            )

            # Try to notify Coordinator conversation about the new team member
            try:
                # Get Coordinator client for this project
                (
                    coordinator_client,
                    coordinator_conversation_id,
                ) = await ConversationClientManager.get_coordinator_client_for_project(context, project_id)

                if coordinator_client and coordinator_conversation_id:
                    # Send notification to Coordinator conversation
                    await coordinator_client.send_messages(
                        NewConversationMessage(
                            content=f"{current_username} has joined the project as a team member.",
                            message_type=MessageType.notice,
                        )
                    )

                    # Log the join in the project log from Coordinator perspective
                    coordinator_context = await ProjectInvitation.create_temporary_context_for_conversation(
                        context, coordinator_conversation_id
                    )
                    if coordinator_context:
                        await ProjectManager.add_log_entry(
                            context=coordinator_context,
                            entry_type=LogEntryType.PARTICIPANT_JOINED,
                            message=f"{current_username} has joined the project as a team member",
                            metadata={
                                "user_id": current_user_id,
                                "user_name": current_username,
                                "joining_conversation_id": str(context.id),
                            },
                        )
            except Exception as e:
                logger.warning(f"Could not notify Coordinator conversation: {e}")
                # This isn't critical, so we continue anyway

            # Get project name for the success message
            try:
                # Try to get the project brief just to verify it exists
                await ProjectManager.get_project_brief(context)

                # Return success with project ID
                return (True, project_id)
            except Exception as e:
                logger.warning(f"Could not get project name: {e}")
                # Return success with project ID even if we couldn't get the name
                return True, project_id

        except Exception as e:
            logger.exception(f"Error joining project: {e}")
            return False, f"Error joining project: {str(e)}"

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

    @staticmethod
    async def process_leave_command(
        context: ConversationContext, message: ConversationMessage, leave_command: str
    ) -> None:
        """
        Processes a leave command from a user.
        Format:
            /{leave_command}

        Leaves the current project.
        """
        # Verify the command format
        content = message.content.strip()
        if not content.startswith(f"/{leave_command}"):
            return

        # Check if this conversation is part of a project
        project_id = await ProjectManager.get_project_id(context)
        if not project_id:
            await context.send_messages(
                NewConversationMessage(
                    content="You are not currently part of a project.",
                    message_type=MessageType.notice,
                )
            )
            return

        # Get the conversation's role in the project
        role = await ProjectManager.get_project_role(context)
        if not role:
            # This shouldn't happen, but handle it gracefully
            await context.send_messages(
                NewConversationMessage(
                    content="You are not currently part of a project.",
                    message_type=MessageType.notice,
                )
            )
            return

        # Clear project association in the conversation context
        # In our new implementation, there's no explicit leave, so we'll just remove the association
        # by removing the conversation role and project files
        try:
            # Get conversation storage directory
            storage_dir = storage_directory_for_context(context)
            role_file = storage_dir / "conversation_role.json"
            project_file = storage_dir / "conversation_project.json"

            # Remove the files if they exist
            if role_file.exists():
                role_file.unlink()
            if project_file.exists():
                project_file.unlink()

            # Log the departure in the project log if possible
            if role == ProjectRole.TEAM:
                # For team members, log to their own context and notify Coordinator
                await ProjectManager.add_log_entry(
                    context=context,
                    entry_type=LogEntryType.PARTICIPANT_LEFT,
                    message="Left the project as team member",
                    metadata={"role": role.value},
                )

                # Try to notify Coordinator
                try:
                    # Get Coordinator conversation ID
                    coordinator_dir = ProjectStorageManager.get_project_dir(project_id) / ProjectRole.COORDINATOR.value
                    if coordinator_dir.exists():
                        role_file = coordinator_dir / "conversation_role.json"
                        if role_file.exists():
                            role_data = read_model(role_file, ProjectRoleData)
                            if role_data:
                                # Get the Coordinator conversation ID
                                coordinator_conversation_id = role_data.conversation_id

                                # Get current user info for the notification
                                current_user_id, current_username = await get_current_user(context)
                                current_username = current_username or "Team member"

                                # Notify Coordinator about the user leaving
                                client = ConversationClientManager.get_conversation_client(
                                    context, coordinator_conversation_id
                                )
                                await client.send_messages(
                                    NewConversationMessage(
                                        content=f"{current_username} has left the project.",
                                        message_type=MessageType.notice,
                                    )
                                )
                except Exception as e:
                    logger.warning(f"Could not notify Coordinator about user leaving: {e}")
                    # Not critical, so we continue

            elif role == ProjectRole.COORDINATOR:
                # For Coordinator, we should notify all team members
                await ProjectManager.add_log_entry(
                    context=context,
                    entry_type=LogEntryType.PARTICIPANT_LEFT,
                    message="Left the project as Coordinator",
                    metadata={"role": role.value},
                )

                # Try to notify all team members
                try:
                    # Get current user info for the notification
                    current_user_id, current_username = await get_current_user(context)
                    current_username = current_username or "Coordinator"

                    # Get all linked conversations
                    linked_conversations = await ConversationProjectManager.get_linked_conversations(context)
                    for conv_id in linked_conversations:
                        try:
                            client = ConversationClientManager.get_conversation_client(context, conv_id)
                            await client.send_messages(
                                NewConversationMessage(
                                    content=f"Coordinator ({current_username}) has left the project. The project is now without a Coordinator.",
                                    message_type=MessageType.notice,
                                )
                            )
                        except Exception:
                            # Skip if we can't notify a particular conversation
                            continue
                except Exception as e:
                    logger.warning(f"Could not notify team members about Coordinator leaving: {e}")
                    # Not critical, so we continue

            # Notify the user of successful leave
            await context.send_messages(
                NewConversationMessage(
                    content="You have left the project successfully.",
                    message_type=MessageType.notice,
                )
            )

        except Exception as e:
            logger.exception(f"Error leaving project: {e}")
            await context.send_messages(
                NewConversationMessage(
                    content=f"Error leaving project: {str(e)}",
                    message_type=MessageType.notice,
                )
            )
