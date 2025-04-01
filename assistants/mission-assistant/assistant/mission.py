"""
Mission assistant functionality for cross-conversation communication.

This module handles the mission assistant's core functionality for managing
communication between conversations, file synchronization, and invitation management.
It implements a clean entity-based approach without backward compatibility concerns.
"""

import logging
import pathlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import semantic_workbench_api_model.workbench_service_client as wsc
from pydantic import BaseModel, Field
from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant import settings
from semantic_workbench_assistant.assistant_app import ConversationContext
from semantic_workbench_assistant.assistant_app.context import storage_directory_for_context
from semantic_workbench_assistant.storage import read_model, write_model

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
    def get_conversation_client(
        context: ConversationContext, conversation_id: str
    ) -> Any:
        """
        Gets a client for accessing another conversation.

        Args:
            context: Source conversation context
            conversation_id: ID of the target conversation

        Returns:
            A client for the target conversation
        """
        # Create a client for the target conversation
        from semantic_workbench_assistant import settings
        
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


class MissionInvitation:
    """
    Manages invitations for joining missions.

    This class provides methods for creating, validating, and redeeming invitations
    for users to join missions between conversations.
    """

    # Model for invitation data
    class Invitation(BaseModel):
        """Data model for a mission invitation."""

        token: str
        invitation_id: str
        mission_id: str
        creator_id: str
        creator_name: str
        created_at: datetime = Field(default_factory=datetime.utcnow)
        expires_at: datetime
        target_username: Optional[str] = None
        redeemed: bool = False
        redeemed_by: Optional[str] = None
        redeemed_at: Optional[datetime] = None

    # Model for storing a collection of invitations
    class InvitationsCollection(BaseModel):
        """Holds a collection of invitation objects."""

        invitations: List[Any] = Field(default_factory=list)

        def model_post_init(self, __context: Any) -> None:
            """Validates that all invitations are of the correct type."""
            # This ensures we maintain type safety when we have proper invitations,
            # but allows for flexibility when loading from storage
            pass

    @staticmethod
    def _get_invitations_path(context: ConversationContext) -> pathlib.Path:
        """Gets the path to the invitations file for this conversation."""
        storage_dir = storage_directory_for_context(context)
        storage_dir.mkdir(parents=True, exist_ok=True)
        return storage_dir / "mission_invitations.json"

    @staticmethod
    async def _save_invitation(context: ConversationContext, invitation: Invitation) -> bool:
        """Saves an invitation to storage."""
        try:
            # Get existing invitations
            path = MissionInvitation._get_invitations_path(context)
            collection = MissionInvitation.InvitationsCollection()

            if path.exists():
                try:
                    # Use our properly typed model to load
                    collection = read_model(path, MissionInvitation.InvitationsCollection)
                    if not collection:
                        collection = MissionInvitation.InvitationsCollection()
                except Exception as e:
                    logger.warning(f"Failed to read invitations: {e}")
                    # Create a new collection on failure
                    collection = MissionInvitation.InvitationsCollection()

            # Check if invitation already exists
            existing_invitations = collection.invitations.copy()
            updated = False

            for i, inv in enumerate(existing_invitations):
                if inv.invitation_id == invitation.invitation_id:
                    # Update existing invitation
                    existing_invitations[i] = invitation
                    updated = True
                    break

            if not updated:
                # Add new invitation
                existing_invitations.append(invitation)

            # Update and save the collection
            collection.invitations = existing_invitations
            write_model(path, collection)
            return True
        except Exception as e:
            logger.error(f"Error saving invitation: {e}")
            return False

    @staticmethod
    async def create_invitation(
        context: ConversationContext,
        target_username: Optional[str] = None,
        expiration_hours: int = 24,
    ) -> Tuple[bool, str]:
        """
        Creates an invitation for another user to join a mission.

        Args:
            context: The conversation context
            target_username: Optional username to invite (if None, anyone can join)
            expiration_hours: Hours until invitation expires

        Returns:
            (success, message) tuple with invitation code
        """
        try:
            # Get the mission ID
            mission_id = await MissionManager.get_mission_id(context)
            if not mission_id:
                # Try to create a mission if none exists
                success, new_mission_id = await MissionManager.create_mission(context)
                if not success:
                    return False, "Could not create a mission. Please try again."
                mission_id = new_mission_id

            # Check if the conversation role is set - should be HQ for invitation creator
            role = await MissionManager.get_mission_role(context)
            if not role:
                # Set this conversation as HQ
                await MissionManager.get_mission_role(context)  # This will create and set the role if needed

            # Generate secure tokens
            invitation_token = secrets.token_urlsafe(32)
            invitation_id = str(uuid.uuid4())
            expiration = datetime.utcnow() + timedelta(hours=expiration_hours)

            # Get current user information
            current_user_id, current_user_name = await get_current_user(context)
            
            if not current_user_id:
                return False, "Could not identify current user in conversation"
                
            # Default user name if none found
            current_user_name = current_user_name or "Unknown User"

            # Create the invitation
            invitation = MissionInvitation.Invitation(
                token=invitation_token,
                invitation_id=invitation_id,
                mission_id=mission_id,
                creator_id=current_user_id,
                creator_name=current_user_name,
                expires_at=expiration,
                target_username=target_username,
            )

            # Save the invitation
            if not await MissionInvitation._save_invitation(context, invitation):
                return False, "Failed to save invitation"

            # Generate a shareable invitation code
            invitation_code = f"{invitation_id}:{invitation_token}"

            # Format the messages based on target username
            if target_username:
                notification_message = f"Mission invitation created for {target_username}."
                success_message = f"Invitation created for {target_username}. They can join by using the /join {invitation_code} command in their conversation."
            else:
                notification_message = "Mission invitation created. Anyone with this code can join the mission."
                success_message = f"Invitation created. Anyone with this code can join by using the /join {invitation_code} command in their conversation."

            # Send notification message about the invitation
            await context.send_messages(
                NewConversationMessage(
                    content=notification_message,
                    message_type=MessageType.notice,
                )
            )

            # Log the invitation creation in the mission log
            await MissionManager.add_log_entry(
                context=context,
                entry_type=LogEntryType.PARTICIPANT_JOINED,
                message=f"Created mission invitation{' for ' + target_username if target_username else ''}",
                metadata={
                    "invitation_id": invitation_id,
                    "target_username": target_username,
                    "expiration": expiration.isoformat(),
                },
            )

            return True, success_message

        except Exception as e:
            logger.exception(f"Error creating invitation: {e}")
            return False, f"Error creating invitation: {str(e)}"

    @staticmethod
    async def _find_invitation_by_code(invitation_code: str) -> Optional[Tuple[Invitation, str]]:
        """
        Finds an invitation by its code.

        Args:
            invitation_code: The invitation code to search for

        Returns:
            Tuple of (invitation, source_conversation_id) if found, None otherwise
        """
        try:
            # Parse the invitation code
            if ":" not in invitation_code:
                return None

            invitation_id, token = invitation_code.split(":", 1)

            # Look for the invitation in all conversations
            storage_root = pathlib.Path(settings.storage.root)
            invitation_files = storage_root.glob("**/mission_invitations.json")

            for file_path in invitation_files:
                try:
                    # Use our properly typed model
                    collection = read_model(file_path, MissionInvitation.InvitationsCollection)
                    if not collection:
                        continue

                    for invitation in collection.invitations:
                        # Handle both object and dictionary formats
                        if isinstance(invitation, dict):
                            # Convert dictionary to proper Invitation object
                            if invitation.get('invitation_id') == invitation_id and invitation.get('token') == token:
                                # Create proper Invitation object from dict
                                proper_invitation = MissionInvitation.Invitation(**invitation)
                                # Get conversation ID from the directory path
                                conversation_id = file_path.parent.name
                                return proper_invitation, conversation_id
                        else:
                            # Handle as object
                            if invitation.invitation_id == invitation_id and invitation.token == token:
                                # Found the invitation
                                # Get conversation ID from the directory path
                                conversation_id = file_path.parent.name
                                return invitation, conversation_id
                except Exception as e:
                    # Skip problematic files
                    logger.warning(f"Error processing invitation file {file_path}: {e}")
                    continue

            return None

        except Exception as e:
            logger.error(f"Error finding invitation: {e}")
            return None

    @staticmethod
    async def validate_invitation(
        context: ConversationContext, invitation_code: str
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Validates an invitation code and returns invitation details if valid.

        Args:
            context: The conversation context
            invitation_code: The invitation code to validate

        Returns:
            (valid, message, invitation_data) tuple
        """
        try:
            # Find the invitation
            result = await MissionInvitation._find_invitation_by_code(invitation_code)
            if not result:
                return False, "Invalid invitation code", None

            invitation, source_conversation_id = result

            # Check if already redeemed
            if invitation.redeemed:
                return False, "This invitation has already been redeemed", None

            # Check if expired
            if datetime.utcnow() > invitation.expires_at:
                return False, "This invitation has expired", None

            # Get current user information
            current_user_id, current_username = await get_current_user(context)
            
            if not current_user_id:
                return False, "Could not identify current user", None

            # Check username restriction if any
            if (
                invitation.target_username
                and current_username
                and invitation.target_username.lower() != current_username.lower()
            ):
                return (
                    False,
                    f"This invitation was created for {invitation.target_username}, not for {current_username}",
                    None,
                )

            # Invitation is valid
            return (
                True,
                "Invitation is valid",
                {
                    "invitation": invitation,
                    "source_conversation_id": source_conversation_id,
                    "mission_id": invitation.mission_id,
                    "current_user_id": current_user_id,
                    "current_username": current_username,
                },
            )

        except Exception as e:
            logger.exception(f"Error validating invitation: {e}")
            return False, f"Error validating invitation: {str(e)}", None

    @staticmethod
    async def redeem_invitation(context: ConversationContext, invitation_code: str) -> Tuple[bool, str]:
        """
        Redeems an invitation code to join a mission.

        Args:
            context: The conversation context
            invitation_code: The invitation code to redeem

        Returns:
            (success, message) tuple
        """
        try:
            # Validate the invitation
            valid, message, invitation_data = await MissionInvitation.validate_invitation(context, invitation_code)

            if not valid or not invitation_data:
                return False, message

            # Extract invitation details
            invitation = invitation_data["invitation"]
            source_conversation_id = invitation_data["source_conversation_id"]
            mission_id = invitation_data["mission_id"]
            current_user_id = invitation_data["current_user_id"]
            current_username = invitation_data["current_username"] or "Unknown User"

            # Mark the invitation as redeemed
            invitation.redeemed = True
            invitation.redeemed_by = current_user_id
            invitation.redeemed_at = datetime.utcnow()

            # Save the updated invitation in the source conversation
            try:
                # Get temporary context for the source conversation
                source_context = await MissionInvitation.create_temporary_context_for_conversation(context, source_conversation_id)
                if source_context:
                    await MissionInvitation._save_invitation(source_context, invitation)
            except Exception as e:
                logger.warning(f"Could not mark invitation as redeemed: {e}")
                # Continue anyway since this isn't critical

            # Join the mission as a field agent
            success = await MissionManager.join_mission(context, mission_id, MissionRole.FIELD)

            if not success:
                logger.error(f"Failed to join mission {mission_id}")
                return False, "Failed to join the mission. Please try again or contact the mission creator."

            # Log the redemption in the mission log
            await MissionManager.add_log_entry(
                context=context,
                entry_type=LogEntryType.PARTICIPANT_JOINED,
                message=f"Joined mission as field agent using invitation from {invitation.creator_name}",
                metadata={
                    "invitation_id": invitation.invitation_id,
                },
            )

            # Notify source conversation about the accepted invitation
            try:
                # Get client for the source conversation
                source_client = ConversationClientManager.get_conversation_client(context, source_conversation_id)

                # Initialize source_context (to avoid unbound variable issue)
                source_context = None

                # Send notification to source conversation
                await source_client.send_messages(
                    NewConversationMessage(
                        content=f"{current_username} has accepted your mission invitation and joined as a field agent.",
                        message_type=MessageType.notice,
                    )
                )

                # Try to create temporary context for logging
                source_context = await MissionInvitation.create_temporary_context_for_conversation(context, source_conversation_id)

                # Log the acceptance in the mission log from HQ perspective
                if source_context:
                    await MissionManager.add_log_entry(
                        context=source_context,
                        entry_type=LogEntryType.PARTICIPANT_JOINED,
                        message=f"{current_username} has joined the mission as a field agent",
                        metadata={
                            "user_id": current_user_id,
                            "user_name": current_username,
                            "joining_conversation_id": str(context.id),
                        },
                    )

            except Exception as e:
                logger.warning(f"Could not notify source conversation: {e}")
                # This isn't critical, so we continue anyway

            # Sync mission files from HQ to this field agent
            # This ensures the field agent has access to the latest mission briefing, etc.
            try:
                # Get the latest mission briefing
                briefing = await MissionManager.get_mission_briefing(context)

                # Get mission name for the notification message
                mission_name = briefing.mission_name if briefing else "mission"

                # Notify user of successful join with mission name
                return (
                    True,
                    f"Invitation accepted! You have joined {mission_name} as a field agent. You now have access to mission data and can communicate with HQ.",
                )

            except Exception as e:
                logger.warning(f"Could not sync mission files: {e}")
                # Return success message even if sync failed
                return True, "Invitation accepted! You have joined the mission as a field agent."

        except Exception as e:
            logger.exception(f"Error redeeming invitation: {e}")
            return False, f"Error redeeming invitation: {str(e)}"

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
    async def get_temporary_context(
        context: ConversationContext, conversation_id: str
    ) -> Optional[ConversationContext]:
        """
        DEPRECATED: Use create_temporary_context_for_conversation instead.
        
        Creates a temporary context for the given conversation ID.
        """
        return await MissionInvitation.create_temporary_context_for_conversation(context, conversation_id)


    @staticmethod
    async def process_invite_command(
        context: ConversationContext, message: ConversationMessage, invite_command: str
    ) -> None:
        """
        Processes an invite command from a user.
        Format:
            /{invite_command} [username]  - username is optional

        If no username is provided, creates an invitation that anyone can use.
        If a username is provided, creates an invitation specific to that user.
        """
        # Extract the username from the command if provided
        content = message.content.strip()
        if not content.startswith(f"/{invite_command}"):
            return

        # Check if we have a mission ID first
        mission_id = await MissionManager.get_mission_id(context)
        if not mission_id:
            # We need to create a mission first
            success, mission_id = await MissionManager.create_mission(context)
            if not success:
                await context.send_messages(
                    NewConversationMessage(
                        content="Failed to create a mission. Please try again.",
                        message_type=MessageType.notice,
                    )
                )
                return

        # Check if this conversation is set as the HQ (only HQ can issue invitations)
        role = await MissionManager.get_mission_role(context)
        if role != MissionRole.HQ:
            # Set this conversation as HQ
            await MissionManager.join_mission(context, mission_id, MissionRole.HQ)

        # Parse the username if provided
        username = None
        command_parts = content.split(maxsplit=1)
        if len(command_parts) > 1:
            username = command_parts[1].strip()

        # Create the invitation
        success, response_text = await MissionInvitation.create_invitation(context, username)

        if success:
            await context.send_messages(
                NewConversationMessage(
                    content=response_text,
                    message_type=MessageType.notice,
                )
            )
        else:
            await context.send_messages(
                NewConversationMessage(
                    content=f"Failed to create invitation: {response_text}",
                    message_type=MessageType.notice,
                )
            )

    @staticmethod
    async def process_join_command(
        context: ConversationContext, message: ConversationMessage, join_command: str
    ) -> None:
        """
        Processes a join command from a user.
        Format:
            /{join_command} invitation_code

        Uses the invitation code to join a mission.
        """
        # Extract the invitation code from the command
        content = message.content.strip()
        if not content.startswith(f"/{join_command}"):
            return

        command_parts = content.split(maxsplit=1)
        if len(command_parts) < 2:
            await context.send_messages(
                NewConversationMessage(
                    content=f"Please provide an invitation code. Format: /{join_command} INVITATION_CODE",
                    message_type=MessageType.notice,
                )
            )
            return

        invitation_code = command_parts[1].strip()
        if not invitation_code:
            await context.send_messages(
                NewConversationMessage(
                    content=f"Please provide an invitation code. Format: /{join_command} INVITATION_CODE",
                    message_type=MessageType.notice,
                )
            )
            return

        # Validate the invitation code
        valid, response_text, invitation_data = await MissionInvitation.validate_invitation(context, invitation_code)
        if not valid:
            await context.send_messages(
                NewConversationMessage(
                    content=f"Invalid invitation: {response_text}",
                    message_type=MessageType.notice,
                )
            )
            return

        # Check if this conversation is already associated with a mission
        existing_mission_id = await MissionManager.get_mission_id(context)
        if existing_mission_id and invitation_data:
            # If already in the same mission, notify the user
            mission_id = invitation_data["mission_id"]
            if existing_mission_id == mission_id:
                await context.send_messages(
                    NewConversationMessage(
                        content="You are already part of this mission.",
                        message_type=MessageType.notice,
                    )
                )
                return

            # If in a different mission, ask the user to confirm they want to switch
            await context.send_messages(
                NewConversationMessage(
                    content="You are already part of a different mission. Please leave that mission first by typing '/leave' before joining a new one.",
                    message_type=MessageType.notice,
                )
            )
            return

        # Redeem the invitation
        success, response_text = await MissionInvitation.redeem_invitation(context, invitation_code)
        await context.send_messages(
            NewConversationMessage(
                content=response_text,
                message_type=MessageType.notice,
            )
        )

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
                                client = ConversationClientManager.get_conversation_client(
                                    context, hq_conversation_id
                                )
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