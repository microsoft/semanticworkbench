"""
Mission manager for the mission assistant.

This module provides the high-level mission management functionality 
that builds on the mission storage architecture.
"""

import logging
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import semantic_workbench_api_model.workbench_service_client as wsc
from pydantic import BaseModel, Field
from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    MessageType,
    NewConversationMessage,
    ParticipantRole,
)
from semantic_workbench_assistant import settings
from semantic_workbench_assistant.assistant_app import ConversationContext
from semantic_workbench_assistant.storage import read_model, write_model

from .artifacts import (
    ArtifactType,
    FieldRequest,
    LogEntry,
    LogEntryType,
    MissionBriefing,
    MissionLog,
    MissionState,
    MissionStatus,
)
from .mission_storage import (
    ConversationMissionManager,
    MissionRole,
    MissionStorageManager,
    MissionStorageReader,
    MissionStorageWriter,
)

logger = logging.getLogger(__name__)


class MissionInvitation(BaseModel):
    """Invitation to join a mission."""
    
    invitation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mission_id: str
    creator_id: str
    creator_name: str
    invitation_token: str
    target_username: Optional[str] = None
    shared_file_ids: List[str] = Field(default_factory=list)
    expires: datetime
    status: str = "pending"  # pending, accepted, expired, revoked
    accepted_by: Optional[str] = None
    accepted_at: Optional[datetime] = None


class MissionManager:
    """High-level manager for mission operations."""
    
    @staticmethod
    async def get_or_create_mission(
        context: ConversationContext, mission_name: str, role: MissionRole
    ) -> str:
        """
        Gets or creates a mission for the conversation.
        
        Args:
            context: The conversation context
            mission_name: Name of the mission
            role: Role of this conversation in the mission
            
        Returns:
            The mission ID
        """
        # Check if conversation is already associated with a mission
        mission_id = await ConversationMissionManager.get_conversation_mission(context)
        
        if mission_id:
            logger.info(f"Conversation {context.id} already associated with mission {mission_id}")
            return mission_id
            
        # Create a new mission ID
        mission_id = str(uuid.uuid4())
        
        # Create mission directory structure
        MissionStorageManager.get_mission_dir(mission_id)
        MissionStorageManager.get_conversation_dir(mission_id, str(context.id), role)
        MissionStorageManager.get_shared_dir(mission_id)
        
        # Create artifact directories
        for artifact_type in ArtifactType:
            MissionStorageManager.get_artifact_dir(mission_id, artifact_type.value)
        
        # Set conversation role and mission association
        await ConversationMissionManager.set_conversation_role(context, mission_id, role)
        await ConversationMissionManager.set_conversation_mission(context, mission_id)
        
        # Initialize mission status
        await MissionManager.initialize_mission_status(context, mission_id, mission_name)
        
        logger.info(f"Created new mission {mission_id} for conversation {context.id} with role {role}")
        return mission_id
    
    @staticmethod
    async def initialize_mission_status(
        context: ConversationContext, mission_id: str, mission_name: str
    ) -> None:
        """
        Initializes the mission status artifact and creates a permanent mission invitation.
        
        Args:
            context: The conversation context
            mission_id: ID of the mission
            mission_name: Name of the mission
        """
        # Get current user information
        participants = await context.get_participants()
        user_id = None
        user_name = "Mission Creator"
        
        for participant in participants.participants:
            if participant.role == ParticipantRole.user:
                user_id = participant.id
                user_name = participant.name
                break
        
        if not user_id:
            user_id = "system"
            
        # Create mission status
        status = MissionStatus(
            artifact_type=ArtifactType.MISSION_STATUS,
            state=MissionState.PLANNING,
            progress_percentage=0,
            created_by=user_id,
            updated_by=user_id,
            conversation_id=str(context.id)
        )
        
        # Save the status
        MissionStorageWriter.write_artifact(
            mission_id=mission_id,
            artifact_type=ArtifactType.MISSION_STATUS.value,
            artifact_id=status.artifact_id,
            artifact=status
        )
        
        # Create initial mission log
        log = MissionLog(
            artifact_type=ArtifactType.MISSION_LOG,
            created_by=user_id,
            updated_by=user_id,
            conversation_id=str(context.id),
            entries=[
                LogEntry(
                    entry_type=LogEntryType.MISSION_STARTED,
                    timestamp=datetime.utcnow(),
                    user_id=user_id,
                    user_name=user_name,
                    message=f"Mission '{mission_name}' created",
                )
            ]
        )
        
        # Save the log
        MissionStorageWriter.write_artifact(
            mission_id=mission_id,
            artifact_type=ArtifactType.MISSION_LOG.value,
            artifact_id=log.artifact_id,
            artifact=log
        )
        
        # Create a permanent mission invitation
        # Set expiration far in the future (10 years)
        long_expiration = datetime.utcnow() + timedelta(days=3650)
        invitation_token = secrets.token_urlsafe(16)  # Shorter token for easier sharing
        
        # Create invitation
        invitation = MissionInvitation(
            mission_id=mission_id,
            creator_id=user_id,
            creator_name=user_name,
            invitation_token=invitation_token,
            target_username=None,  # No username restriction
            shared_file_ids=[],
            expires=long_expiration,
        )
        
        # Save invitation to mission storage
        invitation_dir = MissionStorageManager.get_mission_dir(mission_id) / "invitations"
        invitation_dir.mkdir(exist_ok=True)
        
        invitation_path = invitation_dir / f"{invitation.invitation_id}.json"
        write_model(invitation_path, invitation)
        
        # Log invitation creation
        log.entries.append(
            LogEntry(
                entry_type=LogEntryType.MISSION_STARTED,
                timestamp=datetime.utcnow(),
                user_id=user_id,
                user_name=user_name,
                message="Permanent mission invitation created",
            )
        )
        log.updated_at = datetime.utcnow()
        
        # Update the log
        MissionStorageWriter.write_artifact(
            mission_id=mission_id,
            artifact_type=ArtifactType.MISSION_LOG.value,
            artifact_id=log.artifact_id,
            artifact=log
        )
        
        logger.info(f"Initialized status, log, and permanent invitation for mission {mission_id}")
    
    @staticmethod
    async def get_conversation_role(context: ConversationContext) -> Optional[MissionRole]:
        """
        Gets the role of a conversation in a mission.
        
        Args:
            context: The conversation context
            
        Returns:
            The role, or None if the conversation is not associated with a mission
        """
        return await ConversationMissionManager.get_conversation_role(context)
    
    @staticmethod
    async def get_mission_briefing(context: ConversationContext) -> Optional[MissionBriefing]:
        """
        Gets the mission briefing for the mission associated with the conversation.
        
        Args:
            context: The conversation context
            
        Returns:
            The mission briefing, or None if not found
        """
        mission_id = await ConversationMissionManager.get_conversation_mission(context)
        
        if not mission_id:
            return None
            
        # Get all briefings for this mission
        briefings = MissionStorageReader.read_all_artifacts(
            mission_id=mission_id,
            artifact_type=ArtifactType.MISSION_BRIEFING.value,
            model_class=MissionBriefing
        )
        
        if not briefings:
            return None
            
        # Sort by updated_at, newest first
        briefings.sort(key=lambda b: b.updated_at, reverse=True)
        return briefings[0]
    
    @staticmethod
    async def get_mission_status(context: ConversationContext) -> Optional[MissionStatus]:
        """
        Gets the mission status for the mission associated with the conversation.
        
        Args:
            context: The conversation context
            
        Returns:
            The mission status, or None if not found
        """
        mission_id = await ConversationMissionManager.get_conversation_mission(context)
        
        if not mission_id:
            return None
            
        # Get all statuses for this mission
        statuses = MissionStorageReader.read_all_artifacts(
            mission_id=mission_id,
            artifact_type=ArtifactType.MISSION_STATUS.value,
            model_class=MissionStatus
        )
        
        if not statuses:
            return None
            
        # Sort by updated_at, newest first
        statuses.sort(key=lambda s: s.updated_at, reverse=True)
        return statuses[0]
    
    @staticmethod
    async def get_field_requests(
        context: ConversationContext, include_resolved: bool = False
    ) -> List[FieldRequest]:
        """
        Gets field requests for the mission associated with the conversation.
        
        Args:
            context: The conversation context
            include_resolved: Whether to include resolved requests
            
        Returns:
            List of field requests
        """
        mission_id = await ConversationMissionManager.get_conversation_mission(context)
        
        if not mission_id:
            return []
            
        # Get all requests for this mission
        requests = MissionStorageReader.read_all_artifacts(
            mission_id=mission_id,
            artifact_type=ArtifactType.FIELD_REQUEST.value,
            model_class=FieldRequest
        )
        
        if not include_resolved:
            requests = [r for r in requests if r.status != "resolved"]
            
        # Sort by updated_at, newest first
        requests.sort(key=lambda r: r.updated_at, reverse=True)
        return requests
    
    @staticmethod
    async def create_invitation(
        context: ConversationContext,
        target_username: Optional[str] = None,
        files_to_share: Optional[List[str]] = None,
        expiration_hours: int = 24,
    ) -> Tuple[bool, str, Optional[MissionInvitation]]:
        """
        Creates an invitation for another user to join a mission.
        
        Args:
            context: The conversation context
            target_username: Optional username to invite
            files_to_share: Optional list of file IDs to share
            expiration_hours: Hours until invitation expires
            
        Returns:
            Tuple of (success, message, invitation)
        """
        mission_id = await ConversationMissionManager.get_conversation_mission(context)
        
        if not mission_id:
            return False, "Conversation is not associated with a mission", None
            
        # Get current user information
        participants = await context.get_participants()
        user_id = None
        user_name = "Mission Creator"
        
        for participant in participants.participants:
            if participant.role == ParticipantRole.user:
                user_id = participant.id
                user_name = participant.name
                break
        
        if not user_id:
            return False, "Could not identify current user", None
            
        # Generate invitation token
        invitation_token = secrets.token_urlsafe(32)
        expiration = datetime.utcnow() + timedelta(hours=expiration_hours)
        
        # Create invitation
        invitation = MissionInvitation(
            mission_id=mission_id,
            creator_id=user_id,
            creator_name=user_name,
            invitation_token=invitation_token,
            target_username=target_username,
            shared_file_ids=files_to_share or [],
            expires=expiration,
        )
        
        # Save invitation to mission storage
        invitation_dir = MissionStorageManager.get_mission_dir(mission_id) / "invitations"
        invitation_dir.mkdir(exist_ok=True)
        
        invitation_path = invitation_dir / f"{invitation.invitation_id}.json"
        write_model(invitation_path, invitation)
        
        # Generate invitation code
        invitation_code = f"{invitation.invitation_id}:{invitation_token}"
        
        # Format success message
        if target_username:
            message = f"Invitation created for {target_username}. They can join by using the /join {invitation_code} command in their conversation."
        else:
            message = f"Invitation created. Anyone with this code can join by using the /join {invitation_code} command in their conversation."
        
        # Send notification message about the invitation
        await context.send_messages(
            NewConversationMessage(
                content=f"Mission invitation {invitation.invitation_id} created. Use this code to invite others: {invitation_code}",
                message_type=MessageType.notice,
            )
        )
        
        return True, message, invitation
    
    @staticmethod
    async def validate_invitation(
        context: ConversationContext, invitation_code: str
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Validates an invitation code.
        
        Args:
            context: The conversation context
            invitation_code: The invitation code
            
        Returns:
            Tuple of (valid, message, invitation_data)
        """
        if ":" not in invitation_code:
            return False, "Invalid invitation format", None
            
        invitation_id, token = invitation_code.split(":", 1)
        
        # Search for the invitation in all missions
        missions_root = MissionStorageManager.get_missions_root()
        
        for mission_dir in missions_root.iterdir():
            if not mission_dir.is_dir():
                continue
                
            invitation_dir = mission_dir / "invitations"
            if not invitation_dir.exists():
                continue
                
            invitation_path = invitation_dir / f"{invitation_id}.json"
            if not invitation_path.exists():
                continue
                
            # Found the invitation file, now validate the token
            invitation = read_model(invitation_path, MissionInvitation)
            
            if not invitation:
                continue
                
            if invitation.invitation_token != token:
                return False, "Invalid invitation token", None
                
            # Check if expired
            if datetime.utcnow() > invitation.expires:
                return False, "Invitation has expired", None
                
            # Check if already accepted
            if invitation.status == "accepted":
                return False, "Invitation has already been accepted", None
                
            # Check if target username matches
            if invitation.target_username:
                # Get current user information
                participants = await context.get_participants()
                current_username = None
                
                for participant in participants.participants:
                    if participant.role == ParticipantRole.user:
                        current_username = participant.name
                        break
                
                if current_username and invitation.target_username.lower() != current_username.lower():
                    return False, f"This invitation was created for {invitation.target_username}", None
                    
            # Return invitation data
            return True, "Invitation is valid", {
                "invitation": invitation.model_dump(),
                "mission_id": invitation.mission_id,
            }
            
        return False, "Invitation not found", None
    
    @staticmethod
    async def redeem_invitation(
        context: ConversationContext, invitation_code: str
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Redeems an invitation code to join a mission.
        
        Args:
            context: The conversation context
            invitation_code: The invitation code
            
        Returns:
            Tuple of (success, message, mission_data)
        """
        valid, message, invitation_data = await MissionManager.validate_invitation(context, invitation_code)
        
        if not valid or not invitation_data:
            return False, message, None
            
        invitation = invitation_data["invitation"]
        mission_id = invitation_data["mission_id"]
        
        # Check if conversation already associated with a mission
        existing_mission = await ConversationMissionManager.get_conversation_mission(context)
        
        if existing_mission:
            if existing_mission == mission_id:
                return True, "You are already part of this mission", {"mission_id": mission_id}
            else:
                return False, "This conversation is already part of another mission", None
                
        # Get current user information
        participants = await context.get_participants()
        user_id = None
        user_name = "Field User"
        
        for participant in participants.participants:
            if participant.role == ParticipantRole.user:
                user_id = participant.id
                user_name = participant.name
                break
        
        if not user_id:
            return False, "Could not identify current user", None
            
        # Set up this conversation in the mission
        MissionStorageManager.get_conversation_dir(mission_id, str(context.id), MissionRole.FIELD)
        
        # Set conversation role and mission association
        await ConversationMissionManager.set_conversation_role(context, mission_id, MissionRole.FIELD)
        await ConversationMissionManager.set_conversation_mission(context, mission_id)
        
        # Update conversation metadata to indicate this is a field role
        conversation = await context.get_conversation()
        metadata = conversation.metadata or {}
        metadata["mission_role"] = "field"  # Explicitly set the role in metadata
        
        # Notify workbench UI to refresh role display
        from semantic_workbench_api_model.workbench_model import AssistantStateEvent
        await context.send_conversation_state_event(
            AssistantStateEvent(
                state_id="mission_role",
                event="updated",
                state=None
            )
        )
        
        # Update the invitation status
        invitation_dir = MissionStorageManager.get_mission_dir(mission_id) / "invitations"
        invitation_path = invitation_dir / f"{invitation['invitation_id']}.json"
        
        invitation_obj = read_model(invitation_path, MissionInvitation)
        if invitation_obj:
            invitation_obj.status = "accepted"
            invitation_obj.accepted_by = user_name
            invitation_obj.accepted_at = datetime.utcnow()
            write_model(invitation_path, invitation_obj)
        
        # Add an entry to the mission log
        mission_logs = MissionStorageReader.read_all_artifacts(
            mission_id=mission_id,
            artifact_type=ArtifactType.MISSION_LOG.value,
            model_class=MissionLog
        )
        
        if mission_logs:
            mission_log = mission_logs[0]  # Use the most recent log
            mission_log.entries.append(
                LogEntry(
                    entry_type=LogEntryType.PARTICIPANT_JOINED,
                    timestamp=datetime.utcnow(),
                    user_id=user_id,
                    user_name=user_name,
                    message=f"{user_name} joined the mission as a field operative",
                )
            )
            mission_log.updated_at = datetime.utcnow()
            mission_log.updated_by = user_id
            
            MissionStorageWriter.write_artifact(
                mission_id=mission_id,
                artifact_type=ArtifactType.MISSION_LOG.value,
                artifact_id=mission_log.artifact_id,
                artifact=mission_log
            )
        
        return True, "You have successfully joined the mission", {"mission_id": mission_id}
        
    @staticmethod
    async def list_active_invitations(
        context: ConversationContext,
        include_expired: bool = False
    ) -> List[MissionInvitation]:
        """
        Lists all active invitations for the mission associated with the conversation.
        
        Args:
            context: The conversation context
            include_expired: Whether to include expired invitations (defaults to False)
            
        Returns:
            List of active invitations
        """
        mission_id = await ConversationMissionManager.get_conversation_mission(context)
        
        if not mission_id:
            return []
            
        # Get the invitations directory for this mission
        invitation_dir = MissionStorageManager.get_mission_dir(mission_id) / "invitations"
        
        if not invitation_dir.exists():
            return []
        
        # Read all invitation files
        invitations = []
        for file_path in invitation_dir.glob("*.json"):
            invitation = read_model(file_path, MissionInvitation)
            if invitation:
                # Filter by status (only include pending invitations)
                if invitation.status == "pending":
                    # Check expiration if we're not including expired invitations
                    if include_expired or datetime.utcnow() <= invitation.expires:
                        invitations.append(invitation)
        
        # Sort by creation time (using invitation_id which contains a UUID)
        invitations.sort(key=lambda inv: inv.invitation_id)
        
        return invitations
    
    @staticmethod
    async def process_invite_command(
        context: ConversationContext, message: ConversationMessage, invite_command: str
    ) -> bool:
        """
        Processes an invite command - shows the permanent mission invitation.
        
        Args:
            context: The conversation context
            message: The message containing the command
            invite_command: The command name (e.g., "invite")
            
        Returns:
            True if command was processed, False otherwise
        """
        content = message.content.strip()
        if not content.startswith(f"/{invite_command}"):
            return False
            
        # Get existing invitations
        invitations = await MissionManager.list_active_invitations(context)
        
        if invitations:
            # Use the first invitation - single permanent invitation per mission
            invitation = invitations[0]
            invitation_code = f"{invitation.invitation_id}:{invitation.invitation_token}"
            result_message = (
                "Mission invitation code to share with field operatives:\n\n"
                f"`{invitation_code}`\n\n"
                f"Field operatives can join by using: `/join {invitation_code}`"
            )
            success = True
        else:
            # No invitation found, create a new permanent one
            success, result_message, _ = await MissionManager.create_invitation(
                context, expiration_hours=24*365*10  # ~10 years
            )
            
        # Send response
        await context.send_messages(
            NewConversationMessage(
                content=result_message,
                message_type=MessageType.chat if success else MessageType.notice,
            )
        )
        
        return True
    
    @staticmethod
    async def process_join_command(
        context: ConversationContext, message: ConversationMessage, join_command: str
    ) -> bool:
        """
        Processes a join command.
        
        Args:
            context: The conversation context
            message: The message containing the command
            join_command: The command name (e.g., "join")
            
        Returns:
            True if command was processed, False otherwise
        """
        content = message.content.strip()
        if not content.startswith(f"/{join_command}"):
            return False
            
        parts = content.split(maxsplit=1)
        
        if len(parts) < 2:
            await context.send_messages(
                NewConversationMessage(
                    content=f"Please provide an invitation code. Format: /{join_command} invitation_code",
                    message_type=MessageType.notice,
                )
            )
            return True
            
        invitation_code = parts[1].strip()
        
        success, result_message, _ = await MissionManager.redeem_invitation(context, invitation_code)
        
        # Send response
        await context.send_messages(
            NewConversationMessage(
                content=result_message,
                message_type=MessageType.chat if success else MessageType.notice,
            )
        )
        
        return True


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