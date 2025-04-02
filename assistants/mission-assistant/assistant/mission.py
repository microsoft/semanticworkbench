"""
Mission assistant functionality for cross-conversation communication.

This module handles the mission assistant's core functionality for managing
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

from .mission_data import LogEntryType
from .mission_manager import MissionManager
from .mission_storage import ConversationMissionManager, MissionRole, MissionStorageManager
from .utils import get_current_user


# Define models for mission role data
class MissionRoleData(BaseModel):
    """Data model for storing a conversation's role in a mission."""

    conversation_id: str
    role: MissionRole


logger = logging.getLogger(__name__)


class ConversationClientManager:
    """
    Manages API clients for accessing other conversations.

    This utility class provides methods for creating API clients that can be used
    to send messages to other conversations in the same mission.
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
    async def get_hq_client_for_mission(
        context: ConversationContext, mission_id: str
    ) -> Tuple[Optional[Any], Optional[str]]:
        """
        Gets a client for accessing the HQ conversation for a mission.

        Args:
            context: Source conversation context
            mission_id: ID of the mission

        Returns:
            Tuple of (client, hq_conversation_id) or (None, None) if not found
        """
        from semantic_workbench_assistant.storage import read_model

        from .mission_storage import ConversationMissionManager, MissionRole, MissionStorageManager

        # Look for the HQ conversation directory
        hq_dir = MissionStorageManager.get_mission_dir(mission_id) / MissionRole.HQ.value
        if not hq_dir.exists():
            return None, None

        # Find the role file that contains the conversation ID
        role_file = hq_dir / "conversation_role.json"
        # Try "mission_role.json" as a fallback (old name)
        if not role_file.exists():
            role_file = hq_dir / "mission_role.json"
            if not role_file.exists():
                return None, None

        # Read the role information to get the HQ conversation ID
        role_data = read_model(role_file, ConversationMissionManager.ConversationRoleInfo)
        if not role_data or not role_data.conversation_id:
            return None, None

        # Get the HQ conversation ID
        hq_conversation_id = role_data.conversation_id

        # Don't create a client if the HQ is the current conversation
        if hq_conversation_id == str(context.id):
            return None, hq_conversation_id

        # Create a client for the HQ conversation
        client = ConversationClientManager.get_conversation_client(context, hq_conversation_id)
        return client, hq_conversation_id


class MissionInvitation:
    """
    Manages mission joining.

    Simplified version that uses mission IDs directly as invitation codes.
    """

    # Keeping the minimal models needed for backward compatibility
    class Invitation(BaseModel):
        """Legacy model for a mission invitation - kept for backward compatibility."""
        invitation_id: str
        mission_id: str

    class InvitationsCollection(BaseModel):
        """Legacy model - kept for backward compatibility."""
        invitations: List[Any] = Field(default_factory=list)

    @staticmethod
    def _get_invitations_path(context: ConversationContext) -> pathlib.Path:
        """Legacy method kept for backward compatibility."""
        storage_dir = storage_directory_for_context(context)
        storage_dir.mkdir(parents=True, exist_ok=True)
        return storage_dir / "mission_invitations.json"

    @staticmethod
    async def redeem_invitation(context: ConversationContext, mission_id: str) -> Tuple[bool, str]:
        """
        Joins a mission using its mission ID.
        
        This simplified method treats the mission ID directly as the invitation code,
        eliminating the need for complex invitation generation and validation.

        Args:
            context: The conversation context
            mission_id: The mission ID to join

        Returns:
            (success, message) tuple
        """
        try:
            # Check if mission exists
            if not MissionStorageManager.mission_exists(mission_id):
                return False, f"Mission with ID '{mission_id}' not found. Please check the ID and try again."

            # Get current user information
            current_user_id, current_username = await get_current_user(context)
            current_username = current_username or "Unknown User"

            # Join the mission as a field agent
            success = await MissionManager.join_mission(context, mission_id, MissionRole.FIELD)

            if not success:
                logger.error(f"Failed to join mission {mission_id}")
                return False, "Failed to join the mission. Please try again."

            # Log the join in the mission log
            await MissionManager.add_log_entry(
                context=context,
                entry_type=LogEntryType.PARTICIPANT_JOINED,
                message="Joined mission as field agent",
                metadata={
                    "mission_id": mission_id,
                },
            )

            # Try to notify HQ conversation about the new field agent
            try:
                # Get HQ client for this mission
                hq_client, hq_conversation_id = await ConversationClientManager.get_hq_client_for_mission(
                    context, mission_id
                )
                
                if hq_client and hq_conversation_id:
                    # Send notification to HQ conversation
                    await hq_client.send_messages(
                        NewConversationMessage(
                            content=f"{current_username} has joined the mission as a field agent.",
                            message_type=MessageType.notice,
                        )
                    )

                    # Log the join in the mission log from HQ perspective
                    hq_context = await MissionInvitation.create_temporary_context_for_conversation(
                        context, hq_conversation_id
                    )
                    if hq_context:
                        await MissionManager.add_log_entry(
                            context=hq_context,
                            entry_type=LogEntryType.PARTICIPANT_JOINED,
                            message=f"{current_username} has joined the mission as a field agent",
                            metadata={
                                "user_id": current_user_id,
                                "user_name": current_username,
                                "joining_conversation_id": str(context.id),
                            },
                        )
            except Exception as e:
                logger.warning(f"Could not notify HQ conversation: {e}")
                # This isn't critical, so we continue anyway

            # Get mission name for the success message
            try:
                # Get the latest mission briefing
                briefing = await MissionManager.get_mission_briefing(context)
                
                # Get mission name for the notification message
                mission_name = briefing.mission_name if briefing else "Mission"
                
                return (
                    True, 
                    mission_id
                )
            except Exception as e:
                logger.warning(f"Could not get mission name: {e}")
                # Return success with mission ID even if we couldn't get the name
                return True, mission_id

        except Exception as e:
            logger.exception(f"Error joining mission: {e}")
            return False, f"Error joining mission: {str(e)}"

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

        Leaves the current mission.
        """
        # Verify the command format
        content = message.content.strip()
        if not content.startswith(f"/{leave_command}"):
            return

        # Check if this conversation is part of a mission
        mission_id = await MissionManager.get_mission_id(context)
        if not mission_id:
            await context.send_messages(
                NewConversationMessage(
                    content="You are not currently part of a mission.",
                    message_type=MessageType.notice,
                )
            )
            return

        # Get the conversation's role in the mission
        role = await MissionManager.get_mission_role(context)
        if not role:
            # This shouldn't happen, but handle it gracefully
            await context.send_messages(
                NewConversationMessage(
                    content="You are not currently part of a mission.",
                    message_type=MessageType.notice,
                )
            )
            return

        # Clear mission association in the conversation context
        # In our new implementation, there's no explicit leave, so we'll just remove the association
        # by removing the conversation role and mission files
        try:
            # Get conversation storage directory
            storage_dir = storage_directory_for_context(context)
            role_file = storage_dir / "conversation_role.json"
            mission_file = storage_dir / "conversation_mission.json"

            # Remove the files if they exist
            if role_file.exists():
                role_file.unlink()
            if mission_file.exists():
                mission_file.unlink()

            # Log the departure in the mission log if possible
            if role == MissionRole.FIELD:
                # For field agents, log to their own context and notify HQ
                await MissionManager.add_log_entry(
                    context=context,
                    entry_type=LogEntryType.PARTICIPANT_LEFT,
                    message="Left the mission as field agent",
                    metadata={"role": role.value},
                )

                # Try to notify HQ
                try:
                    # Get HQ conversation ID
                    hq_dir = MissionStorageManager.get_mission_dir(mission_id) / MissionRole.HQ.value
                    if hq_dir.exists():
                        role_file = hq_dir / "conversation_role.json"
                        if role_file.exists():
                            role_data = read_model(role_file, MissionRoleData)
                            if role_data:
                                # Get the HQ conversation ID
                                hq_conversation_id = role_data.conversation_id

                                # Get current user info for the notification
                                current_user_id, current_username = await get_current_user(context)
                                current_username = current_username or "Field agent"

                                # Notify HQ about the user leaving
                                client = ConversationClientManager.get_conversation_client(context, hq_conversation_id)
                                await client.send_messages(
                                    NewConversationMessage(
                                        content=f"{current_username} has left the mission.",
                                        message_type=MessageType.notice,
                                    )
                                )
                except Exception as e:
                    logger.warning(f"Could not notify HQ about user leaving: {e}")
                    # Not critical, so we continue

            elif role == MissionRole.HQ:
                # For HQ, we should notify all field agents
                await MissionManager.add_log_entry(
                    context=context,
                    entry_type=LogEntryType.PARTICIPANT_LEFT,
                    message="Left the mission as HQ",
                    metadata={"role": role.value},
                )

                # Try to notify all field agents
                try:
                    # Get current user info for the notification
                    current_user_id, current_username = await get_current_user(context)
                    current_username = current_username or "HQ"

                    # Get all linked conversations
                    linked_conversations = await ConversationMissionManager.get_linked_conversations(context)
                    for conv_id in linked_conversations:
                        try:
                            client = ConversationClientManager.get_conversation_client(context, conv_id)
                            await client.send_messages(
                                NewConversationMessage(
                                    content=f"HQ ({current_username}) has left the mission. The mission is now without an HQ.",
                                    message_type=MessageType.notice,
                                )
                            )
                        except Exception:
                            # Skip if we can't notify a particular conversation
                            continue
                except Exception as e:
                    logger.warning(f"Could not notify field agents about HQ leaving: {e}")
                    # Not critical, so we continue

            # Notify the user of successful leave
            await context.send_messages(
                NewConversationMessage(
                    content="You have left the mission successfully.",
                    message_type=MessageType.notice,
                )
            )

        except Exception as e:
            logger.exception(f"Error leaving mission: {e}")
            await context.send_messages(
                NewConversationMessage(
                    content=f"Error leaving mission: {str(e)}",
                    message_type=MessageType.notice,
                )
            )
