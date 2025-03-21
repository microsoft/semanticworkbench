"""
Mission assistant functionality for file sharing between conversations.
"""

import io
import logging
import pathlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

import semantic_workbench_api_model.workbench_service_client as wsc
from pydantic import BaseModel, Field
from semantic_workbench_api_model.workbench_model import (
    AssistantStateEvent,
    ConversationMessage,
    ConversationPermission,
    MessageType,
    NewConversationMessage,
    NewConversationShare,
    ParticipantRole,
)
from semantic_workbench_assistant import settings
from semantic_workbench_assistant.assistant_app import ConversationContext
from semantic_workbench_assistant.assistant_app.context import storage_directory_for_context
from semantic_workbench_assistant.storage import read_model, write_model

logger = logging.getLogger(__name__)


# Data models for state management
class LinkedFile(BaseModel):
    """Information about a linked file."""

    filename: str
    last_synced: Optional[str] = None
    read_only: bool = False


class LinkedConversation(BaseModel):
    """Information about a linked conversation."""

    conversation_id: str
    status: str = "active"  # active, pending, inactive
    user_id: str
    user_name: str = ""
    files: List[LinkedFile] = Field(default_factory=list)
    pending_invitations: List[Dict[str, Any]] = Field(default_factory=list)


class ConversationLinks(BaseModel):
    """Collection of linked conversations for a conversation."""

    linked_conversations: Dict[str, LinkedConversation] = Field(default_factory=dict)


class MissionStateManager:
    """Manages persistent state for mission conversations."""

    @staticmethod
    def get_state_file_path(context: ConversationContext) -> pathlib.Path:
        """Gets the path to the state file for this conversation."""
        storage_dir = storage_directory_for_context(context)
        storage_dir.mkdir(parents=True, exist_ok=True)
        return storage_dir / "mission_links.json"

    @staticmethod
    async def get_links(context: ConversationContext) -> ConversationLinks:
        """Gets the conversation links for this conversation."""
        path = MissionStateManager.get_state_file_path(context)
        try:
            if path.exists():
                return read_model(path, ConversationLinks) or ConversationLinks()
            return ConversationLinks()
        except Exception as e:
            logger.error(f"Error reading conversation links: {e}")
            return ConversationLinks()

    @staticmethod
    async def save_links(context: ConversationContext, links: ConversationLinks) -> None:
        """Saves the conversation links for this conversation."""
        path = MissionStateManager.get_state_file_path(context)
        try:
            write_model(path, links)
        except Exception as e:
            logger.error(f"Error saving conversation links: {e}")


class ConversationClientManager:
    """Manages API clients for accessing other conversations."""

    @staticmethod
    def get_conversation_client(context: ConversationContext, target_conversation_id: str) -> wsc.ConversationAPIClient:
        """
        Creates an API client for another conversation.
        This allows cross-conversation operations.
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


class FileSynchronizer:
    """Handles file synchronization between linked conversations."""

    @staticmethod
    async def sync_file(context: ConversationContext, target_conversation_id: str, filename: str) -> bool:
        """
        Synchronizes a file from the current conversation to a target conversation.

        Args:
            context: Current conversation context
            target_conversation_id: ID of the conversation to sync with
            filename: Name of the file to synchronize

        Returns:
            bool: True if successfully synchronized, False otherwise
        """
        try:
            # Get the target conversation client
            target_client = ConversationClientManager.get_conversation_client(context, target_conversation_id)

            # Download file from current conversation
            file_content = io.BytesIO()
            async with context.read_file(filename) as stream:
                async for chunk in stream:
                    file_content.write(chunk)
            file_content.seek(0)

            # Get metadata about the file
            file_response = await context.get_files()
            source_file = next((f for f in file_response.files if f.filename == filename), None)

            if not source_file:
                logger.error(f"File {filename} not found in source conversation")
                return False

            # Upload to target conversation
            await target_client.write_file(
                filename=filename,
                file_content=file_content,
                content_type=source_file.content_type or "application/octet-stream",
            )

            # Update the "last_synced" timestamp in both conversations' state
            now = datetime.utcnow().isoformat()
            source_links = await MissionStateManager.get_links(context)

            # Update all relevant linked conversations to mark this file as synced
            for conv_id, linked_conv in source_links.linked_conversations.items():
                for file in linked_conv.files:
                    if file.filename == filename:
                        file.last_synced = now

            await MissionStateManager.save_links(context, source_links)
            return True

        except Exception as e:
            logger.exception(f"Error synchronizing file: {e}")
            return False

    @staticmethod
    async def get_files_to_sync(context: ConversationContext, target_conversation_id: str) -> Set[str]:
        """
        Gets the list of files that should be synchronized with the target conversation.

        Args:
            context: Current conversation context
            target_conversation_id: ID of conversation to check against

        Returns:
            Set of filenames that should be synchronized
        """
        links = await MissionStateManager.get_links(context)
        linked_conv = links.linked_conversations.get(target_conversation_id)

        if not linked_conv or linked_conv.status != "active":
            return set()

        # If no specific files are listed, all files should be synced
        if not linked_conv.files:
            files_response = await context.get_files()
            return {file.filename for file in files_response.files}

        # Otherwise, return only the specific files
        return {file.filename for file in linked_conv.files}


class FileVersionManager:
    """Manages file versions and synchronization across conversations."""

    @staticmethod
    async def get_file_version_info(context: ConversationContext, filename: str) -> dict:
        """Gets version information for a file in the current conversation."""
        try:
            files_response = await context.get_files()
            file_info = next((f for f in files_response.files if f.filename == filename), None)

            if not file_info:
                return {"exists": False}

            # The File model contains version information
            return {
                "exists": True,
                "version": file_info.current_version,
                "last_modified": file_info.updated_datetime,
                "size": file_info.file_size,
                "content_type": file_info.content_type,
            }
        except Exception as e:
            logger.error(f"Error getting file version info: {e}")
            return {"exists": False, "error": str(e)}

    @staticmethod
    async def detect_conflicts(
        source_context: ConversationContext,
        target_client: wsc.ConversationAPIClient,
        filename: str,
        last_synced: Optional[str],
    ) -> dict:
        """Detects if there are conflicts between source and target versions."""
        source_info = await FileVersionManager.get_file_version_info(source_context, filename)

        # Check if target file exists
        try:
            target_files = await target_client.get_files()
            target_file = next((f for f in target_files.files if f.filename == filename), None)

            if not target_file:
                return {"has_conflict": False, "target_exists": False}

            if not last_synced:
                # If never synced before, just consider it a conflict if target exists
                return {"has_conflict": True, "reason": "initial_sync_with_existing_target"}

            # Parse ISO timestamps for comparison
            last_synced_time = datetime.fromisoformat(last_synced.replace("Z", "+00:00"))
            source_modified = datetime.fromisoformat(str(source_info["last_modified"]).replace("Z", "+00:00"))
            target_modified = datetime.fromisoformat(str(target_file.updated_datetime).replace("Z", "+00:00"))

            # Check if both source and target were modified since last sync
            if source_modified > last_synced_time and target_modified > last_synced_time:
                return {
                    "has_conflict": True,
                    "reason": "both_modified",
                    "source_modified": source_modified.isoformat(),
                    "target_modified": target_modified.isoformat(),
                    "last_synced": last_synced,
                }

            return {"has_conflict": False}

        except Exception as e:
            logger.error(f"Error detecting conflicts: {e}")
            return {"has_conflict": False, "error": str(e)}


class MissionInvitation:
    """Manages invitations between conversations for the mission assistant."""

    @staticmethod
    async def create_invitation(
        context: ConversationContext,
        target_username: str,
        files_to_share: Optional[List[str]] = None,
        expiration_hours: int = 24,
        permission: str = "read_write",
    ) -> Tuple[bool, str]:
        """
        Creates an invitation for another user to join a mission.

        Args:
            context: The conversation context
            target_username: Username to invite
            files_to_share: List of filenames to share (None for all)
            expiration_hours: Hours until invitation expires
            permission: Permission level for the invited user

        Returns:
            (success, message) tuple
        """
        try:
            # Generate a secure invitation token
            invitation_token = secrets.token_urlsafe(32)
            expiration = datetime.utcnow() + timedelta(hours=expiration_hours)

            # First check if target user exists
            participants = await context.get_participants()
            current_user_id = None

            for participant in participants.participants:
                if participant.role == ParticipantRole.user:
                    # Store the current user's ID to mark them as invitation creator
                    current_user_id = participant.id
                    break

            if not current_user_id:
                return False, "Could not identify current user in conversation"

            # Get files information if needed
            files_metadata = []
            if files_to_share:
                files_response = await context.get_files()
                for filename in files_to_share:
                    file_info = next((f for f in files_response.files if f.filename == filename), None)
                    if file_info:
                        files_metadata.append({
                            "filename": filename,
                            "version": file_info.current_version,
                            "content_type": file_info.content_type,
                        })

            # Create invitation metadata
            invitation_metadata = {
                "mission_invitation": True,
                "invitation_token": invitation_token,
                "invitation_expires": expiration.isoformat(),
                "target_username": target_username,
                "invitation_creator_id": current_user_id,
                "files_to_share": files_metadata if files_to_share else [],
                "share_all_files": files_to_share is None,
            }

            # Create a conversation share using the Workbench API
            share = NewConversationShare(
                conversation_id=uuid.UUID(context.id),
                label=f"Mission Invitation for {target_username}",
                conversation_permission=ConversationPermission(permission),
                metadata=invitation_metadata,
            )

            # Since we don't have direct access to the share methods through the client builders,
            # we'll need to use context.client which has been set up for us
            from semantic_workbench_assistant import settings
            
            # Create a direct HTTP client for the workbench service
            import httpx
            async with httpx.AsyncClient(base_url=str(settings.workbench_service_url)) as client:
                # Add appropriate headers
                client.headers.update({
                    "X-Assistant-Service-ID": context.assistant._assistant_service_id,
                    "X-API-Key": settings.workbench_service_api_key,
                    "X-Assistant-ID": str(context.assistant.id)
                })
                
                # Send the request directly
                response = await client.post(
                    f"/assistant-service-conversations/{context.id}/shares",
                    json=share.model_dump(exclude_defaults=True, exclude_unset=True, mode="json")
                )
                response.raise_for_status()
                share_result = response.json()

            if share_result:
                # Store the invitation in our local state as well
                links = await MissionStateManager.get_links(context)

                # Initialize conversation entry if needed
                conversation_id = str(context.id)
                if conversation_id not in links.linked_conversations:
                    links.linked_conversations[conversation_id] = LinkedConversation(
                        conversation_id=conversation_id, status="active", user_id=current_user_id, files=[]
                    )

                # Add pending invitation to state
                linked_conversation = links.linked_conversations[conversation_id]
                linked_conversation.pending_invitations.append({
                    "token": invitation_token,
                    "share_id": str(share_result.id),
                    "target_username": target_username,
                    "expires": expiration.isoformat(),
                    "files_to_share": files_to_share or [],
                })

                await MissionStateManager.save_links(context, links)

                # Generate a shareable invitation code
                invitation_code = f"{share_result.id}:{invitation_token}"

                return (
                    True,
                    f"Invitation created for {target_username}. They can join by using the /join {invitation_code} command in their conversation.",
                )

            return False, "Failed to create invitation share"

        except Exception as e:
            logger.exception(f"Error creating invitation: {e}")
            return False, f"Error creating invitation: {str(e)}"

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
            # Parse the invitation code
            if ":" not in invitation_code:
                return False, "Invalid invitation format", None

            share_id_str, token = invitation_code.split(":", 1)

            try:
                share_id = uuid.UUID(share_id_str)
            except ValueError:
                return False, "Invalid share ID in invitation", None

            # Get the share using the Workbench API
            try:
                # Create direct HTTP client for the workbench service
                from semantic_workbench_assistant import settings
                import httpx
                
                async with httpx.AsyncClient(base_url=str(settings.workbench_service_url)) as client:
                    # Add appropriate headers
                    client.headers.update({
                        "X-Assistant-Service-ID": context.assistant._assistant_service_id,
                        "X-API-Key": settings.workbench_service_api_key,
                        "X-Assistant-ID": str(context.assistant.id)
                    })
                    
                    # Send the request directly
                    response = await client.get(f"/shares/{share_id}")
                    response.raise_for_status()
                    share_data = response.json()
                    
                    # Create a ConversationShare object from the response
                    from semantic_workbench_api_model.workbench_model import ConversationShare
                    share = ConversationShare.model_validate(share_data)
            except Exception:
                return False, "Invitation not found or expired", None

            if not share:
                return False, "Invitation not found", None

            # Get invitation metadata
            metadata = share.metadata or {}
            if not metadata.get("mission_invitation"):
                return False, "Not a valid mission invitation", None

            # Verify the token matches
            if metadata.get("invitation_token") != token:
                return False, "Invalid invitation token", None

            # Check if invitation has expired
            invitation_expires = metadata.get("invitation_expires")
            if invitation_expires:
                expires = datetime.fromisoformat(invitation_expires.replace("Z", "+00:00"))
                if datetime.utcnow() > expires:
                    return False, "Invitation has expired", None

            # Get current user information - needed regardless for the return value
            participants = await context.get_participants()
            current_username = None
            current_user_id = None

            for participant in participants.participants:
                if participant.role == ParticipantRole.user:
                    current_username = participant.name
                    current_user_id = participant.id
                    break
            
            # Make sure we found a user
            if not current_user_id:
                return False, "Could not identify current user", None
                
            # Verify username matches the target (if specified)
            target_username = metadata.get("target_username")
            if target_username and current_username and target_username.lower() != current_username.lower():
                return False, f"This invitation was created for {target_username}, not for {current_username}", None

            # Invitation is valid, return the share data
            return (
                True,
                "Invitation is valid",
                {
                    "share": share,
                    "source_conversation_id": str(share.conversation_id),
                    "current_user_id": current_user_id,
                    "files_to_share": metadata.get("files_to_share", []),
                    "share_all_files": metadata.get("share_all_files", False),
                    "permission": share.conversation_permission,
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

            # Get the share details
            share = invitation_data["share"]
            source_conversation_id = invitation_data["source_conversation_id"]
            current_user_id = invitation_data["current_user_id"]
            files_to_share = invitation_data["files_to_share"]
            share_all_files = invitation_data["share_all_files"]

            # Redeem the share
            try:
                # Create direct HTTP client for the workbench service
                from semantic_workbench_assistant import settings
                import httpx
                
                async with httpx.AsyncClient(base_url=str(settings.workbench_service_url)) as client:
                    # Add appropriate headers
                    client.headers.update({
                        "X-Assistant-Service-ID": context.assistant._assistant_service_id,
                        "X-API-Key": settings.workbench_service_api_key,
                        "X-Assistant-ID": str(context.assistant.id)
                    })
                    
                    # Send the request directly
                    response = await client.post(f"/shares/{share.id}/redemptions")
                    response.raise_for_status()
                    redemption_data = response.json()
                    
                    # Create a ConversationShareRedemption object from the response
                    from semantic_workbench_api_model.workbench_model import ConversationShareRedemption
                    redemption = ConversationShareRedemption.model_validate(redemption_data)
            except Exception as e:
                return False, f"Failed to redeem invitation: {str(e)}"

            if not redemption:
                return False, "Failed to redeem invitation"

            # Create a link from this conversation to the source conversation
            links = await MissionStateManager.get_links(context)

            # Setup the current conversation in link state
            conversation_id = str(context.id)
            if conversation_id not in links.linked_conversations:
                links.linked_conversations[conversation_id] = LinkedConversation(
                    conversation_id=conversation_id, status="active", user_id=current_user_id, files=[]
                )

            # Add the source conversation to our links
            file_list = []
            if source_conversation_id not in links.linked_conversations:
                links.linked_conversations[source_conversation_id] = LinkedConversation(
                    conversation_id=source_conversation_id, status="active", user_id=str(share.owner_id), files=[]
                )

                # Add the appropriate files to track
                if share_all_files:
                    # Track all files from source
                    files_response = await context.get_files()
                    file_list = [LinkedFile(filename=file.filename) for file in files_response.files]
                else:
                    # Track only specified files
                    file_list = [LinkedFile(filename=file["filename"]) for file in files_to_share]

                links.linked_conversations[source_conversation_id].files = file_list

            # Save the updated links
            await MissionStateManager.save_links(context, links)

            # Now create a message to the source conversation about the accepted invitation
            # This requires getting a client for the source conversation
            try:
                source_client = ConversationClientManager.get_conversation_client(context, source_conversation_id)

                # Get participants from this conversation
                participants = await context.get_participants()
                current_username = None

                for participant in participants.participants:
                    if participant.role == ParticipantRole.user:
                        current_username = participant.name
                        break

                # Send notification to source conversation
                await source_client.send_messages(
                    NewConversationMessage(
                        content=f"{current_username} has accepted your mission invitation. Files will now be synchronized between conversations.",
                        message_type=MessageType.notice,
                    )
                )

                # Also update the source conversation's links to include this conversation
                # We'll need to get their state, modify it, and save it
                source_context = await MissionInvitation.get_temporary_context(context, source_conversation_id)
                if source_context:
                    source_links = await MissionStateManager.get_links(source_context)

                    # Add this conversation to their links if not already there
                    if conversation_id not in source_links.linked_conversations:
                        source_links.linked_conversations[conversation_id] = LinkedConversation(
                            conversation_id=conversation_id, status="active", user_id=current_user_id, files=file_list
                        )

                    # Update pending invitations to mark this one as accepted
                    linked_source_conv = source_links.linked_conversations.get(source_conversation_id)
                    pending_invitations = linked_source_conv.pending_invitations if linked_source_conv else []

                    for invitation in pending_invitations:
                        if invitation.get("share_id") == str(share.id):
                            invitation["status"] = "accepted"
                            invitation["accepted_by"] = current_username
                            invitation["accepted_time"] = datetime.utcnow().isoformat()

                    await MissionStateManager.save_links(source_context, source_links)

            except Exception as e:
                logger.warning(f"Could not notify source conversation: {e}")
                # This isn't critical, so we continue anyway

            return (
                True,
                "Invitation accepted! You are now part of the mission and files will be synchronized between conversations.",
            )

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


class MissionManager:
    """Manages linked conversations and file synchronization."""

    @staticmethod
    async def get_linked_conversations(context: ConversationContext) -> Dict[str, Any]:
        """
        Gets the linked conversations data from the assistant metadata.
        Returns an empty dict if no linked conversations exist.
        """
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
            AssistantStateEvent(
                state_id="linked_conversations",
                event="updated",
                state=None
            )
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
        linked_conversations = await MissionManager.get_linked_conversations(context)
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

        await MissionManager.save_linked_conversations(context, linked_conversations)
        logger.info(f"Linked conversation {conversation_id} with {target_conversation_id}")

    @staticmethod
    async def should_sync_file(context: ConversationContext, filename: str) -> List[str]:
        """
        Checks if a file should be synchronized and returns the list of
        conversation IDs to sync with.
        """
        linked_conversations = await MissionManager.get_linked_conversations(context)
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
        Format: /invite username
        """
        # Extract the username from the command
        content = message.content.strip()
        if not content.startswith(f"/{invite_command}"):
            return

        parts = content.split(maxsplit=1)
        if len(parts) < 2:
            await context.send_messages(
                NewConversationMessage(
                    content=f"Please specify a username to invite. Format: /{invite_command} username",
                    message_type=MessageType.notice,
                )
            )
            return

        username = parts[1].strip()

        # Create a secure invitation using our new mechanism
        success, result_message = await MissionInvitation.create_invitation(
            context=context,
            target_username=username,
            files_to_share=None,  # Share all files
        )

        # Send the message to the user
        await context.send_messages(
            NewConversationMessage(content=result_message, message_type=MessageType.chat if success else MessageType.notice)
        )

        logger.info(f"Invitation command processed for {username}: {success}")

    @staticmethod
    async def process_join_command(
        context: ConversationContext, message: ConversationMessage, join_command: str
    ) -> None:
        """
        Processes a join command from a user.
        Format: /join invitation_code
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
        success, result_message = await MissionInvitation.redeem_invitation(context=context, invitation_code=invitation_code)

        # Send the message to the user
        await context.send_messages(
            NewConversationMessage(content=result_message, message_type=MessageType.chat if success else MessageType.notice)
        )

        logger.info(f"Join command processed with code {invitation_code}: {success}")
