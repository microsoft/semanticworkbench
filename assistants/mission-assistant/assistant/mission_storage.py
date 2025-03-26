"""
Mission storage management module.

Provides functions for working with the mission storage structure:
- Missions
- HQ and Field conversation data
- Shared artifacts
"""

import logging
import pathlib
from enum import Enum
from typing import Optional

from semantic_workbench_assistant import settings
from semantic_workbench_assistant.assistant_app import ConversationContext
from semantic_workbench_assistant.assistant_app.context import storage_directory_for_context
from semantic_workbench_assistant.storage import read_model, write_model

logger = logging.getLogger(__name__)


class MissionRole(str, Enum):
    """Role of a conversation in a mission."""
    HQ = "hq"
    FIELD = "field"


class MissionStorageManager:
    """Manages storage paths and access for mission data."""

    MISSIONS_ROOT = "missions"

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
    def get_shared_dir(mission_id: str) -> pathlib.Path:
        """Gets the shared directory for a mission."""
        mission_dir = MissionStorageManager.get_mission_dir(mission_id)
        shared_dir = mission_dir / "shared"
        shared_dir.mkdir(parents=True, exist_ok=True)
        return shared_dir

    @staticmethod
    def get_artifact_dir(mission_id: str, artifact_type: str) -> pathlib.Path:
        """
        Gets the directory for a specific artifact type in the shared directory.
        
        Args:
            mission_id: ID of the mission
            artifact_type: Type of artifact (e.g., 'briefing', 'kb', 'requests', 'log')
            
        Returns:
            Path to the artifact directory
        """
        shared_dir = MissionStorageManager.get_shared_dir(mission_id)
        artifact_dir = shared_dir / artifact_type
        artifact_dir.mkdir(parents=True, exist_ok=True)
        return artifact_dir

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


class MissionStorageReader:
    """Provides read operations for mission storage."""
    
    @staticmethod
    def read_artifact(mission_id: str, artifact_type: str, artifact_id: str, model_class):
        """
        Reads an artifact from the mission storage.
        
        Args:
            mission_id: ID of the mission
            artifact_type: Type of artifact (e.g., 'briefing', 'kb', 'requests', 'log')
            artifact_id: ID of the specific artifact
            model_class: Pydantic model class for the artifact
            
        Returns:
            The artifact as a Pydantic model, or None if not found
        """
        artifact_dir = MissionStorageManager.get_artifact_dir(mission_id, artifact_type)
        artifact_path = artifact_dir / f"{artifact_id}.json"
        return read_model(artifact_path, model_class)
    
    @staticmethod
    def read_all_artifacts(mission_id: str, artifact_type: str, model_class):
        """
        Reads all artifacts of a specific type from the mission storage.
        
        Args:
            mission_id: ID of the mission
            artifact_type: Type of artifact (e.g., 'briefing', 'kb', 'requests', 'log')
            model_class: Pydantic model class for the artifacts
            
        Returns:
            List of artifacts as Pydantic models
        """
        artifact_dir = MissionStorageManager.get_artifact_dir(mission_id, artifact_type)
        artifacts = []
        
        if not artifact_dir.exists():
            return artifacts
            
        for file_path in artifact_dir.glob("*.json"):
            artifact = read_model(file_path, model_class)
            if artifact:
                artifacts.append(artifact)
                
        return artifacts


class MissionStorageWriter:
    """Provides write operations for mission storage."""
    
    @staticmethod
    def write_artifact(mission_id: str, artifact_type: str, artifact_id: str, artifact):
        """
        Writes an artifact to the mission storage.
        
        Args:
            mission_id: ID of the mission
            artifact_type: Type of artifact (e.g., 'briefing', 'kb', 'requests', 'log')
            artifact_id: ID of the specific artifact
            artifact: Pydantic model instance to write
            
        Returns:
            Path to the written artifact
        """
        artifact_dir = MissionStorageManager.get_artifact_dir(mission_id, artifact_type)
        artifact_path = artifact_dir / f"{artifact_id}.json"
        write_model(artifact_path, artifact)
        return artifact_path
    
    @staticmethod
    def delete_artifact(mission_id: str, artifact_type: str, artifact_id: str) -> bool:
        """
        Deletes an artifact from the mission storage.
        
        Args:
            mission_id: ID of the mission
            artifact_type: Type of artifact
            artifact_id: ID of the specific artifact
            
        Returns:
            True if the artifact was deleted, False otherwise
        """
        artifact_dir = MissionStorageManager.get_artifact_dir(mission_id, artifact_type)
        artifact_path = artifact_dir / f"{artifact_id}.json"
        
        if artifact_path.exists():
            artifact_path.unlink()
            return True
        
        return False


class ConversationMissionManager:
    """Manages the association between conversations and missions."""
    
    from pydantic import BaseModel, Field
    
    class ConversationRoleInfo(BaseModel):
        """Stores a conversation's role in a mission."""
        mission_id: str
        role: MissionRole
        
    class MissionAssociation(BaseModel):
        """Stores a conversation's mission association."""
        mission_id: str
        
    @staticmethod
    async def set_conversation_role(context: ConversationContext, mission_id: str, role: MissionRole) -> None:
        """
        Sets the role of a conversation in a mission.
        
        Args:
            context: Conversation context
            mission_id: ID of the mission
            role: Role of the conversation (HQ or FIELD)
        """
        role_data = ConversationMissionManager.ConversationRoleInfo(mission_id=mission_id, role=role)
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
    async def set_conversation_mission(context: ConversationContext, mission_id: str) -> None:
        """
        Associates a conversation with a mission.
        
        Args:
            context: Conversation context
            mission_id: ID of the mission
        """
        mission_data = ConversationMissionManager.MissionAssociation(mission_id=mission_id)
        mission_path = MissionStorageManager.get_conversation_mission_file_path(context)
        write_model(mission_path, mission_data)
        
    @staticmethod
    async def get_conversation_mission(context: ConversationContext) -> Optional[str]:
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