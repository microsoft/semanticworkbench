"""
Mission storage management module.

Provides direct access to mission data with a clean, simple storage approach.
"""

import logging
import pathlib
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from semantic_workbench_assistant import settings
from semantic_workbench_assistant.assistant_app import ConversationContext
from semantic_workbench_assistant.assistant_app.context import storage_directory_for_context
from semantic_workbench_assistant.storage import read_model, write_model

from .utils import get_current_user

from .mission_data import (
    FieldRequest,
    LogEntry,
    LogEntryType,
    MissionBriefing,
    MissionKB,
    MissionLog,
    MissionStatus,
)

logger = logging.getLogger(__name__)


class MissionRole(str, Enum):
    """Role of a conversation in a mission."""

    HQ = "hq"
    FIELD = "field"


class MissionStorageManager:
    """Manages storage paths and access for mission data."""

    MISSIONS_ROOT = "missions"

    # Define standard entity types and their file names
    MISSION_BRIEFING = "mission_briefing"
    MISSION_LOG = "mission_log"
    MISSION_STATUS = "mission_status"
    MISSION_KB = "mission_kb"
    FIELD_REQUEST = "field_request"

    # Predefined entity types that have a single instance per mission
    PREDEFINED_ENTITIES = {
        MISSION_BRIEFING: "briefing.json",
        MISSION_LOG: "log.json",
        MISSION_STATUS: "status.json",
        MISSION_KB: "kb.json",
    }

    @staticmethod
    def get_missions_root() -> pathlib.Path:
        """Gets the root path for all missions."""
        return pathlib.Path(settings.storage.root) / MissionStorageManager.MISSIONS_ROOT

    @staticmethod
    def get_mission_dir(mission_id: str) -> pathlib.Path:
        """Gets the directory for a specific mission."""
        missions_root = MissionStorageManager.get_missions_root()
        mission_dir = missions_root / mission_id
        mission_dir.mkdir(parents=True, exist_ok=True)
        return mission_dir

    @staticmethod
    def get_shared_dir(mission_id: str) -> pathlib.Path:
        """Gets the shared directory for a mission."""
        mission_dir = MissionStorageManager.get_mission_dir(mission_id)
        shared_dir = mission_dir / "shared"
        shared_dir.mkdir(parents=True, exist_ok=True)
        return shared_dir

    @staticmethod
    def get_entity_dir(mission_id: str, entity_type: str) -> pathlib.Path:
        """Gets the directory for a specific entity type in the shared directory."""
        shared_dir = MissionStorageManager.get_shared_dir(mission_id)
        entity_dir = shared_dir / entity_type
        entity_dir.mkdir(parents=True, exist_ok=True)
        return entity_dir

    @staticmethod
    def get_conversation_dir(mission_id: str, conversation_id: str, role: MissionRole) -> pathlib.Path:
        """
        Gets the directory for a specific conversation within a mission.

        Args:
            mission_id: ID of the mission
            conversation_id: ID of the conversation
            role: Role of the conversation (HQ or FIELD)

        Returns:
            Path to the conversation directory
        """
        mission_dir = MissionStorageManager.get_mission_dir(mission_id)

        # For HQ conversations, use the role as directory name
        if role == MissionRole.HQ:
            conv_dir = mission_dir / role.value
        else:
            # For field conversations, prefix the conversation ID with 'field_'
            conv_dir = mission_dir / f"field_{conversation_id}"

        conv_dir.mkdir(parents=True, exist_ok=True)
        return conv_dir

    @staticmethod
    def get_briefing_path(mission_id: str) -> pathlib.Path:
        """Gets the path to the mission briefing file."""
        entity_dir = MissionStorageManager.get_entity_dir(mission_id, MissionStorageManager.MISSION_BRIEFING)
        return entity_dir / MissionStorageManager.PREDEFINED_ENTITIES[MissionStorageManager.MISSION_BRIEFING]

    @staticmethod
    def get_mission_log_path(mission_id: str) -> pathlib.Path:
        """Gets the path to the mission log file."""
        entity_dir = MissionStorageManager.get_entity_dir(mission_id, MissionStorageManager.MISSION_LOG)
        return entity_dir / MissionStorageManager.PREDEFINED_ENTITIES[MissionStorageManager.MISSION_LOG]

    @staticmethod
    def get_mission_status_path(mission_id: str) -> pathlib.Path:
        """Gets the path to the mission status file."""
        entity_dir = MissionStorageManager.get_entity_dir(mission_id, MissionStorageManager.MISSION_STATUS)
        return entity_dir / MissionStorageManager.PREDEFINED_ENTITIES[MissionStorageManager.MISSION_STATUS]

    @staticmethod
    def get_mission_kb_path(mission_id: str) -> pathlib.Path:
        """Gets the path to the mission knowledge base file."""
        entity_dir = MissionStorageManager.get_entity_dir(mission_id, MissionStorageManager.MISSION_KB)
        return entity_dir / MissionStorageManager.PREDEFINED_ENTITIES[MissionStorageManager.MISSION_KB]

    @staticmethod
    def get_field_request_path(mission_id: str, request_id: str) -> pathlib.Path:
        """Gets the path to a field request file."""
        entity_dir = MissionStorageManager.get_entity_dir(mission_id, MissionStorageManager.FIELD_REQUEST)
        return entity_dir / f"{request_id}.json"

    @staticmethod
    def get_field_requests_dir(mission_id: str) -> pathlib.Path:
        """Gets the directory containing all field requests."""
        return MissionStorageManager.get_entity_dir(mission_id, MissionStorageManager.FIELD_REQUEST)

    @staticmethod
    def mission_exists(mission_id: str) -> bool:
        """Checks if a mission exists."""
        mission_dir = MissionStorageManager.get_missions_root() / mission_id
        return mission_dir.exists()

    @staticmethod
    def get_conversation_role_file_path(context: ConversationContext) -> pathlib.Path:
        """Gets the path to the file that stores a conversation's role in missions."""
        storage_dir = storage_directory_for_context(context)
        storage_dir.mkdir(parents=True, exist_ok=True)
        return storage_dir / "mission_role.json"

    @staticmethod
    def get_conversation_mission_file_path(context: ConversationContext) -> pathlib.Path:
        """Gets the path to the file that stores a conversation's mission association."""
        storage_dir = storage_directory_for_context(context)
        storage_dir.mkdir(parents=True, exist_ok=True)
        return storage_dir / "mission_association.json"


class MissionStorage:
    """Unified storage operations for mission data."""

    @staticmethod
    def read_mission_briefing(mission_id: str) -> Optional[MissionBriefing]:
        """Reads the mission briefing."""
        path = MissionStorageManager.get_briefing_path(mission_id)
        return read_model(path, MissionBriefing)

    @staticmethod
    def write_mission_briefing(mission_id: str, briefing: MissionBriefing) -> pathlib.Path:
        """Writes the mission briefing."""
        path = MissionStorageManager.get_briefing_path(mission_id)
        write_model(path, briefing)
        return path

    @staticmethod
    def read_mission_log(mission_id: str) -> Optional[MissionLog]:
        """Reads the mission log."""
        path = MissionStorageManager.get_mission_log_path(mission_id)
        return read_model(path, MissionLog)

    @staticmethod
    def write_mission_log(mission_id: str, log: MissionLog) -> pathlib.Path:
        """Writes the mission log."""
        path = MissionStorageManager.get_mission_log_path(mission_id)
        write_model(path, log)
        return path

    @staticmethod
    def read_mission_status(mission_id: str) -> Optional[MissionStatus]:
        """Reads the mission status."""
        path = MissionStorageManager.get_mission_status_path(mission_id)
        return read_model(path, MissionStatus)

    @staticmethod
    def write_mission_status(mission_id: str, status: MissionStatus) -> pathlib.Path:
        """Writes the mission status."""
        path = MissionStorageManager.get_mission_status_path(mission_id)
        write_model(path, status)
        return path

    @staticmethod
    def read_mission_kb(mission_id: str) -> Optional[MissionKB]:
        """Reads the mission knowledge base."""
        path = MissionStorageManager.get_mission_kb_path(mission_id)
        return read_model(path, MissionKB)

    @staticmethod
    def write_mission_kb(mission_id: str, kb: MissionKB) -> pathlib.Path:
        """Writes the mission knowledge base."""
        path = MissionStorageManager.get_mission_kb_path(mission_id)
        write_model(path, kb)
        return path

    @staticmethod
    def read_field_request(mission_id: str, request_id: str) -> Optional[FieldRequest]:
        """Reads a field request."""
        path = MissionStorageManager.get_field_request_path(mission_id, request_id)
        return read_model(path, FieldRequest)

    @staticmethod
    def write_field_request(mission_id: str, request: FieldRequest) -> pathlib.Path:
        """Writes a field request."""
        # Field requests must have an ID
        if not request.request_id:
            raise ValueError("Field request must have a request_id")

        path = MissionStorageManager.get_field_request_path(mission_id, request.request_id)
        write_model(path, request)
        return path

    @staticmethod
    def get_all_field_requests(mission_id: str) -> List[FieldRequest]:
        """Gets all field requests for a mission."""
        dir_path = MissionStorageManager.get_field_requests_dir(mission_id)
        requests = []

        if not dir_path.exists():
            return requests

        for file_path in dir_path.glob("*.json"):
            request = read_model(file_path, FieldRequest)
            if request:
                requests.append(request)

        # Sort by updated_at timestamp, newest first
        requests.sort(key=lambda r: r.updated_at, reverse=True)
        return requests

    @staticmethod
    async def notify_ui_update(context: ConversationContext) -> None:
        """Notifies the UI to refresh the mission state."""
        from semantic_workbench_api_model.workbench_model import AssistantStateEvent

        await context.send_conversation_state_event(
            AssistantStateEvent(
                state_id="mission_status",  # Must match the inspector_state_providers key in chat.py
                event="updated",
                state=None,
            )
        )
        
    @staticmethod
    async def get_linked_conversations(context: ConversationContext) -> List[str]:
        """
        Gets all conversation IDs linked to the same mission as the current conversation.
        
        Args:
            context: Current conversation context
            
        Returns:
            List of conversation IDs
        """
        mission_id = await ConversationMissionManager.get_conversation_mission(context)
        if not mission_id:
            return []
            
        # For now, a simplified implementation that just returns the conversation itself
        # In a real implementation, you would query all conversations associated with this mission
        return [str(context.id)]

    @staticmethod
    async def log_mission_event(
        context: ConversationContext,
        mission_id: str,
        entry_type: str,
        message: str,
        related_entity_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Logs an event to the mission log.

        Args:
            context: Current conversation context
            mission_id: ID of the mission
            entry_type: Type of log entry
            message: Log message
            related_entity_id: Optional ID of a related entity (e.g., field request)
            metadata: Optional additional metadata

        Returns:
            True if the log entry was added successfully, False otherwise
        """
        # Get user information
        user_id, user_name = await get_current_user(context)
        
        if not user_id:
            return False
            
        # Default user name if none found
        user_name = user_name or "Unknown User"

        # Create a log entry
        entry = LogEntry(
            entry_type=LogEntryType(entry_type),
            message=message,
            user_id=user_id,
            user_name=user_name,
            related_entity_id=related_entity_id,
            metadata=metadata or {},
        )

        # Get existing log or create a new one
        log = MissionStorage.read_mission_log(mission_id)
        if not log:
            # Create a new mission log
            log = MissionLog(
                created_by=user_id,
                updated_by=user_id,
                conversation_id=str(context.id),
                entries=[],
            )

        # Add the entry and update metadata
        log.entries.append(entry)
        log.updated_at = datetime.utcnow()
        log.updated_by = user_id
        log.version += 1

        # Save the updated log
        MissionStorage.write_mission_log(mission_id, log)
        return True


class MissionNotifier:
    """Handles notifications between conversations for mission updates."""

    @staticmethod
    async def notify_linked_conversations(context: ConversationContext, mission_id: str, message: str) -> None:
        """
        Notifies all linked conversations about an update.

        Args:
            context: Current conversation context
            mission_id: ID of the mission
            message: Notification message to send
        """
        from semantic_workbench_api_model.workbench_model import MessageType, NewConversationMessage

        from .mission import ConversationClientManager

        # Get conversation IDs in the same mission
        linked_conversations = await MissionStorage.get_linked_conversations(context)
        current_conversation_id = str(context.id)

        # Send notification to each linked conversation
        for conv_id in linked_conversations:
            if conv_id != current_conversation_id:
                try:
                    # Get client for the target conversation
                    client = ConversationClientManager.get_conversation_client(context, conv_id)

                    # Send the notification
                    await client.send_messages(
                        NewConversationMessage(
                            content=message,
                            message_type=MessageType.notice,
                        )
                    )
                except Exception as e:
                    logger.error(f"Failed to notify conversation {conv_id}: {e}")

    @staticmethod
    async def notify_mission_update(
        context: ConversationContext, mission_id: str, update_type: str, message: str
    ) -> None:
        """
        Notifies the current conversation and all linked conversations about a mission update.
        Also updates the UI state.

        Args:
            context: Current conversation context
            mission_id: ID of the mission
            update_type: Type of update (e.g., 'briefing', 'status', 'field_request', etc.)
            message: Notification message
        """
        from semantic_workbench_api_model.workbench_model import MessageType, NewConversationMessage

        # Notify the current conversation
        await context.send_messages(
            NewConversationMessage(
                content=message,
                message_type=MessageType.notice,
            )
        )

        # Notify linked conversations
        await MissionNotifier.notify_linked_conversations(context, mission_id, message)

        # Update the UI
        await MissionStorage.notify_ui_update(context)


class ConversationMissionManager:
    """Manages the association between conversations and missions."""

    from pydantic import BaseModel, Field

    class ConversationRoleInfo(BaseModel):
        """Stores a conversation's role in a mission."""

        mission_id: str
        role: MissionRole
        conversation_id: str

    class MissionAssociation(BaseModel):
        """Stores a conversation's mission association."""

        mission_id: str
        
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
            mission_id = await ConversationMissionManager.get_conversation_mission(context)
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
                        role_data = read_model(role_file, ConversationMissionManager.ConversationRoleInfo)
                        if role_data and role_data.conversation_id != conversation_id:
                            result.append(role_data.conversation_id)
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

    @staticmethod
    async def set_conversation_role(context: ConversationContext, mission_id: str, role: MissionRole) -> None:
        """
        Sets the role of a conversation in a mission.

        Args:
            context: Conversation context
            mission_id: ID of the mission
            role: Role of the conversation (HQ or FIELD)
        """
        role_data = ConversationMissionManager.ConversationRoleInfo(
            mission_id=mission_id, 
            role=role,
            conversation_id=str(context.id)
        )
        role_path = MissionStorageManager.get_conversation_role_file_path(context)
        write_model(role_path, role_data)

    @staticmethod
    async def get_conversation_role(context: ConversationContext) -> Optional[MissionRole]:
        """
        Gets the role of a conversation in a mission.

        Args:
            context: Conversation context

        Returns:
            The role, or None if not associated with a mission
        """
        role_path = MissionStorageManager.get_conversation_role_file_path(context)
        role_data = read_model(role_path, ConversationMissionManager.ConversationRoleInfo)

        if role_data:
            return role_data.role

        return None

    @staticmethod
    async def associate_conversation_with_mission(context: ConversationContext, mission_id: str) -> None:
        """
        Associates a conversation with a mission.

        Args:
            context: Conversation context
            mission_id: ID of the mission to associate with
        """
        mission_data = ConversationMissionManager.MissionAssociation(mission_id=mission_id)
        mission_path = MissionStorageManager.get_conversation_mission_file_path(context)
        write_model(mission_path, mission_data)

    @staticmethod
    async def get_associated_mission_id(context: ConversationContext) -> Optional[str]:
        """
        Gets the mission ID associated with a conversation.

        Args:
            context: Conversation context

        Returns:
            The mission ID, or None if not associated with a mission
        """
        mission_path = MissionStorageManager.get_conversation_mission_file_path(context)
        mission_data = read_model(mission_path, ConversationMissionManager.MissionAssociation)

        if mission_data:
            return mission_data.mission_id

        return None
        
    # Maintain backwards compatibility with existing code
    # These methods are deprecated and should be removed in a future update
    @staticmethod
    async def set_conversation_mission(context: ConversationContext, mission_id: str) -> None:
        """
        DEPRECATED: Use associate_conversation_with_mission instead.
        
        Associates a conversation with a mission.
        """
        await ConversationMissionManager.associate_conversation_with_mission(context, mission_id)
        
    @staticmethod
    async def get_conversation_mission(context: ConversationContext) -> Optional[str]:
        """
        DEPRECATED: Use get_associated_mission_id instead.
        
        Gets the mission ID associated with a conversation.
        """
        return await ConversationMissionManager.get_associated_mission_id(context)
