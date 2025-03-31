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
    AssistantStateEvent,
    ConversationMessage,
    MessageType,
    NewConversationMessage,
    ParticipantRole,
)
from semantic_workbench_assistant import settings
from semantic_workbench_assistant.assistant_app import ConversationContext
from semantic_workbench_assistant.assistant_app.context import storage_directory_for_context
from semantic_workbench_assistant.storage import read_model, write_model

from .mission_data import LogEntryType
from .mission_manager import MissionManager
from .mission_storage import MissionRole, MissionStorageManager


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
    to interact with other conversations in a mission.
    """

    @staticmethod
    def get_conversation_client(context: ConversationContext, target_conversation_id: str) -> wsc.ConversationAPIClient:
        """
        Creates an API client for another conversation.
        This allows cross-conversation operations.

        Args:
            context: The current conversation context
            target_conversation_id: ID of the target conversation

        Returns:
            ConversationAPIClient that can be used to interact with the target conversation
        """
        # Get the assistant_id from the current context
        assistant_id = context.assistant.id

        # Create a new client using the same builder but for a different conversation
        client_builder = wsc.WorkbenchServiceClientBuilder(
            base_url=str(settings.workbench_service_url),
            assistant_service_id=context.assistant._assistant_service_id,
            api_key=settings.workbench_service_api_key,
        )

        return client_builder.for_conversation(assistant_id=assistant_id, conversation_id=target_conversation_id)

    @staticmethod
    async def get_temporary_context(
        context: ConversationContext, conversation_id: str
    ) -> Optional[ConversationContext]:
        """
        Creates a temporary context for another conversation.
        This is used for operations that need context methods rather than just the client.

        Args:
            context: The current conversation context
            conversation_id: The ID of the conversation to create a context for

        Returns:
            A temporary conversation context or None if creation failed
        """
        try:
            # Get client for the target conversation
            target_client = ConversationClientManager.get_conversation_client(context, conversation_id)

            # To create a temporary context, we need the conversation details and the assistant details
            conversation = await target_client.get_conversation()
            if not conversation:
                return None

            # We'll use the same assistant as in the current context
            assistant = context.assistant

            # Create a temporary context with the same properties as the original
            # but pointing to a different conversation
            from semantic_workbench_assistant.assistant_app.context import ConversationContext

            temp_context = ConversationContext(
                assistant=assistant,
                id=conversation_id,
                title=conversation.title,
            )

            return temp_context

        except Exception as e:
            logger.error(f"Error creating temporary context: {e}")
            return None

    @staticmethod
    async def get_linked_conversations(context: ConversationContext) -> List[str]:
        """
        Gets all conversations linked to this one through the same mission.

        Args:
            context: Current conversation context

        Returns:
            List of conversation IDs that are part of the same mission
        """
        try:
            # Get mission ID
            mission_id = await MissionManager.get_mission_id(context)
            if not mission_id:
                return []

            # Get all conversation role files in the storage
            mission_dir = MissionStorageManager.get_mission_dir(mission_id)
            if not mission_dir.exists():
                return []

            # Look for conversation directories
            result = []
            conversation_id = str(context.id)

            # Check HQ directory
            hq_dir = mission_dir / MissionRole.HQ.value
            if hq_dir.exists():
                # If this isn't the current conversation, add it
                role_file = hq_dir / "mission_role.json"
                if role_file.exists():
                    try:
                        # Use our properly defined MissionRoleData model
                        data = read_model(role_file, MissionRoleData)
                        if data and data.conversation_id != conversation_id:
                            result.append(data.conversation_id)
                    except Exception:
                        pass

            # Check field directories
            for field_dir in mission_dir.glob("field_*"):
                if field_dir.is_dir():
                    # Extract conversation ID from directory name
                    field_id = field_dir.name[6:]  # Remove "field_" prefix
                    if field_id != conversation_id:
                        result.append(field_id)

            return result

        except Exception as e:
            logger.error(f"Error getting linked conversations: {e}")
            return []


class FileVersionManager:
    """
    Manages file versions and conflict detection between conversations.

    This utility class provides methods for tracking file versions and detecting
    conflicts when synchronizing files between conversations.
    """

    @staticmethod
    async def get_file_info(context: ConversationContext, filename: str) -> Optional[Dict[str, Any]]:
        """
        Gets file information for a file in the current conversation.

        Args:
            context: Current conversation context
            filename: Name of the file to get information for

        Returns:
            Dictionary with file information if the file exists, None otherwise
        """
        try:
            files_response = await context.list_files()
            file_info = next((f for f in files_response.files if f.filename == filename), None)

            if not file_info:
                return None

            # The File model contains version information
            return {
                "filename": filename,
                "version": file_info.current_version,
                "last_modified": file_info.updated_datetime,
                "size": file_info.file_size,
                "content_type": file_info.content_type,
            }
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return None

    @staticmethod
    async def detect_conflicts(
        source_context: ConversationContext,
        target_context: ConversationContext,
        filename: str,
    ) -> Dict[str, Any]:
        """
        Detects if there are conflicts between file versions in different conversations.

        Args:
            source_context: Source conversation context
            target_context: Target conversation context
            filename: Name of the file to check

        Returns:
            Dictionary with conflict information
        """
        try:
            # Get source file info
            source_info = await FileVersionManager.get_file_info(source_context, filename)
            if not source_info:
                return {"has_conflict": False, "source_exists": False}

            # Get target file info
            target_info = await FileVersionManager.get_file_info(target_context, filename)
            if not target_info:
                return {"has_conflict": False, "target_exists": False}

            # With the direct storage approach, we don't need to track sync status
            # of individual files since mission data is in shared storage.
            # This simplifies conflict detection significantly.

            # Compare versions to determine if there's a potential conflict
            if source_info["version"] != target_info["version"]:
                return {
                    "has_conflict": True,
                    "reason": "version_mismatch",
                    "source_version": source_info["version"],
                    "target_version": target_info["version"],
                }

            # No conflict detected
            return {
                "has_conflict": False,
                "source_exists": True,
                "target_exists": True,
                "source_version": source_info["version"],
                "target_version": target_info["version"],
            }

        except Exception as e:
            logger.error(f"Error detecting conflicts: {e}")
            return {"has_conflict": False, "error": str(e)}


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
            participants = await context.get_participants()
            current_user_id = None
            current_user_name = "Unknown User"

            for participant in participants.participants:
                if participant.role == ParticipantRole.user:
                    current_user_id = participant.id
                    current_user_name = participant.name
                    break

            if not current_user_id:
                return False, "Could not identify current user in conversation"

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
                        if invitation.invitation_id == invitation_id and invitation.token == token:
                            # Found the invitation
                            # Get conversation ID from the directory path
                            conversation_id = file_path.parent.name
                            return invitation, conversation_id
                except Exception:
                    # Skip problematic files
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
            participants = await context.get_participants()
            current_username = None
            current_user_id = None

            for participant in participants.participants:
                if participant.role == ParticipantRole.user:
                    current_username = participant.name
                    current_user_id = participant.id
                    break

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
                source_context = await MissionInvitation.get_temporary_context(context, source_conversation_id)
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
                source_context = await MissionInvitation.get_temporary_context(context, source_conversation_id)

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
    async def get_temporary_context(
        context: ConversationContext, conversation_id: str
    ) -> Optional[ConversationContext]:
        """
        Creates a temporary context for another conversation.
        This is used for operations that need context methods rather than just the client.

        Args:
            context: The current conversation context
            conversation_id: The ID of the conversation to create a context for

        Returns:
            A temporary conversation context or None if creation failed
        """
        try:
            # Get client for the target conversation
            target_client = ConversationClientManager.get_conversation_client(context, conversation_id)

            # To create a temporary context, we need:
            # 1. The conversation details
            # 2. The assistant details
            conversation = await target_client.get_conversation()
            if not conversation:
                return None

            # We'll use the same assistant as in the current context
            assistant = context.assistant

            # Create a temporary context with the same properties as the original
            # but pointing to a different conversation
            from semantic_workbench_assistant.assistant_app.context import ConversationContext

            temp_context = ConversationContext(
                assistant=assistant,
                id=conversation_id,
                title=context.title,
            )

            return temp_context

        except Exception as e:
            logger.error(f"Error creating temporary context: {e}")
            return None


class LegacyMissionManager:
    """
    Legacy class for managing linked conversations and file synchronization.

    This class is maintained for backward compatibility and will be gradually
    migrated to the new MissionManager implementation. It redirects to the new
    implementation where possible while maintaining compatibility with existing code.
    """

    @staticmethod
    async def get_linked_conversations(context: ConversationContext) -> Dict[str, Any]:
        """
        Gets the linked conversations data from the assistant metadata.
        Returns an empty dict if no linked conversations exist.
        """
        # Try to get mission_id from the new implementation first
        mission_id = await MissionManager.get_mission_id(context)
        if mission_id:
            # In the future, we could translate from the new model to the old format
            # For now, just check if we have legacy data
            pass

        # Fall back to old metadata storage
        conversation = await context.get_conversation()
        metadata = conversation.metadata or {}
        return metadata.get("linked_conversations", {})

    @staticmethod
    async def save_linked_conversations(context: ConversationContext, linked_conversations: Dict[str, Any]) -> None:
        """Saves the linked conversations data to the assistant metadata."""
        conversation = await context.get_conversation()
        metadata = conversation.metadata or {}
        metadata["linked_conversations"] = linked_conversations
        await context.send_conversation_state_event(
            AssistantStateEvent(state_id="linked_conversations", event="updated", state=None)
        )

        # Also update the UI for mission_status if we have mission_id
        mission_id = await MissionManager.get_mission_id(context)
        if mission_id:
            await context.send_conversation_state_event(
                AssistantStateEvent(state_id="mission_status", event="updated", state=None)
            )

    @staticmethod
    async def link_conversation(
        context: ConversationContext,
        target_conversation_id: str,
        user_id: str,
        files_to_sync: Optional[List[str]] = None,
    ) -> None:
        """
        Links a conversation to the current conversation for file sharing.

        Args:
            context: The conversation context
            target_conversation_id: The ID of the conversation to link
            user_id: The ID of the user in the target conversation
            files_to_sync: Optional list of filenames to sync (defaults to all)
        """
        # For backwards compatibility, we'll stick with the legacy approach for now
        # In the future, we could use the mission_id from MissionManager.get_mission_id(context)

        linked_conversations = await LegacyMissionManager.get_linked_conversations(context)
        conversation_id = str(context.id)

        # Initialize if this is the first linked conversation
        if conversation_id not in linked_conversations:
            linked_conversations[conversation_id] = {
                "status": "active",
                "users": [],
                "files": files_to_sync or [],
                "links": [],
            }

        # Add the target conversation if not already linked
        if target_conversation_id not in linked_conversations:
            linked_conversations[target_conversation_id] = {
                "status": "active",
                "users": [user_id],
                "files": files_to_sync or [],
                "links": [conversation_id],
            }
        else:
            # Update existing target conversation
            target_data = linked_conversations[target_conversation_id]
            if user_id not in target_data["users"]:
                target_data["users"].append(user_id)
            if conversation_id not in target_data["links"]:
                target_data["links"].append(conversation_id)
            # Update files to sync if provided
            if files_to_sync:
                for file in files_to_sync:
                    if file not in target_data["files"]:
                        target_data["files"].append(file)

        # Update source conversation to link to target
        source_data = linked_conversations[conversation_id]
        if target_conversation_id not in source_data["links"]:
            source_data["links"].append(target_conversation_id)

        await LegacyMissionManager.save_linked_conversations(context, linked_conversations)
        logger.info(f"Linked conversation {conversation_id} with {target_conversation_id}")

    @staticmethod
    async def should_sync_file(context: ConversationContext, filename: str) -> List[str]:
        """
        Checks if a file should be synchronized and returns the list of
        conversation IDs to sync with.
        """
        # Note: In a future update, we would implement a state management approach
        # For now, we'll use the legacy conversation metadata approach directly

        # Fall back to legacy approach if no data from new implementation
        linked_conversations = await LegacyMissionManager.get_linked_conversations(context)
        conversation_id = str(context.id)

        if conversation_id not in linked_conversations:
            return []

        target_conversations = []
        source_data = linked_conversations[conversation_id]

        # If no specific files are listed, sync all files
        if not source_data["files"] or filename in source_data["files"]:
            for linked_id in source_data["links"]:
                if linked_id in linked_conversations:
                    linked_data = linked_conversations[linked_id]
                    if linked_data["status"] == "active":
                        # Check if the linked conversation should receive this file
                        if not linked_data["files"] or filename in linked_data["files"]:
                            target_conversations.append(linked_id)

        return target_conversations

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
            success, new_mission_id = await MissionManager.create_mission(context)
            if not success:
                await context.send_messages(
                    NewConversationMessage(
                        content="Could not create a mission. Please try again.",
                        message_type=MessageType.notice,
                    )
                )
                return

            # Set this conversation as the HQ
            await MissionManager.get_mission_role(context)  # This will set the role

        parts = content.split(maxsplit=1)

        # If no username specified, create a universal invitation
        if len(parts) < 2:
            # Create a secure invitation without username restriction
            success, result_message = await MissionInvitation.create_invitation(context=context)
        else:
            # Create a secure invitation for a specific username
            username = parts[1].strip()
            success, result_message = await MissionInvitation.create_invitation(
                context=context, target_username=username
            )

        # Send the message to the user
        await context.send_messages(
            NewConversationMessage(
                content=result_message, message_type=MessageType.chat if success else MessageType.notice
            )
        )

        username_info = parts[1].strip() if len(parts) > 1 else "anyone"
        logger.info(f"Invitation command processed for {username_info}: {success}")

    @staticmethod
    async def process_join_command(
        context: ConversationContext, message: ConversationMessage, join_command: str
    ) -> None:
        """
        Processes a join command from a user.
        Format:
            /{join_command} invitation_code

        Redeems the invitation and joins the mission as a field agent.
        """
        # Extract the invitation code from the command
        content = message.content.strip()
        if not content.startswith(f"/{join_command}"):
            return

        parts = content.split(maxsplit=1)
        if len(parts) < 2:
            await context.send_messages(
                NewConversationMessage(
                    content=f"Please provide an invitation code. Format: /{join_command} invitation_code",
                    message_type=MessageType.notice,
                )
            )
            return

        invitation_code = parts[1].strip()

        # Redeem the invitation
        success, result_message = await MissionInvitation.redeem_invitation(
            context=context, invitation_code=invitation_code
        )

        # Send the message to the user
        await context.send_messages(
            NewConversationMessage(
                content=result_message, message_type=MessageType.chat if success else MessageType.notice
            )
        )

        logger.info(f"Join command processed with code {invitation_code}: {success}")

    @staticmethod
    async def process_status_command(
        context: ConversationContext, message: ConversationMessage, status_command: str
    ) -> None:
        """
        Processes a mission status command from a user.
        Format:
            /{status_command}

        Displays the current mission status to the user.
        """
        # Verify this is the status command
        content = message.content.strip()
        if not content.startswith(f"/{status_command}"):
            return

        # Get mission ID
        mission_id = await MissionManager.get_mission_id(context)
        if not mission_id:
            await context.send_messages(
                NewConversationMessage(
                    content="You are not currently part of a mission.",
                    message_type=MessageType.notice,
                )
            )
            return

        # Get mission status
        status = await MissionManager.get_mission_status(context)
        if not status:
            await context.send_messages(
                NewConversationMessage(
                    content="No mission status available.",
                    message_type=MessageType.notice,
                )
            )
            return

        # Get mission briefing
        briefing = await MissionManager.get_mission_briefing(context)

        # Format the status message
        mission_name = briefing.mission_name if briefing else "Current Mission"
        status_state = status.state.value if status.state else "Unknown"
        progress = status.progress_percentage

        # Build the status message
        status_message = f"## {mission_name} Status\n\n"
        status_message += f"**State:** {status_state}\n"
        status_message += f"**Progress:** {progress}%\n"

        if status.status_message:
            status_message += f"**Message:** {status.status_message}\n"

        if status.next_actions and len(status.next_actions) > 0:
            status_message += "\n**Next Actions:**\n"
            for i, action in enumerate(status.next_actions):
                status_message += f"{i + 1}. {action}\n"

        # Show active blockers if any
        if status.active_blockers and len(status.active_blockers) > 0:
            requests = await MissionManager.get_field_requests(context)
            blocker_requests = [r for r in requests if r.request_id in status.active_blockers]

            if blocker_requests:
                status_message += "\n**Active Blockers:**\n"
                for req in blocker_requests:
                    status_message += f"- {req.title} (Priority: {req.priority.value})\n"

        # Send the formatted status message
        await context.send_messages(NewConversationMessage(content=status_message, message_type=MessageType.chat))
