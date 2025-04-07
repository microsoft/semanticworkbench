"""
Project storage management module.

Provides direct access to project data with a clean, simple storage approach.
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
from pydantic import BaseModel, Field

from .utils import get_current_user

from .project_data import (
    InformationRequest,
    LogEntry,
    LogEntryType,
    ProjectBrief,
    ProjectKB,
    ProjectLog,
    ProjectDashboard,
)

logger = logging.getLogger(__name__)


class ProjectRole(str, Enum):
    """Role of a conversation in a project."""

    COORDINATOR = "coordinator"
    TEAM = "team"


class CoordinatorConversationMessage(BaseModel):
    """Model for storing a message from Coordinator conversation for Team access."""

    message_id: str
    content: str
    sender_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_assistant: bool = False


class CoordinatorConversationStorage(BaseModel):
    """Model for storing a collection of Coordinator conversation messages."""

    project_id: str
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    messages: List[CoordinatorConversationMessage] = Field(default_factory=list)


class ProjectStorageManager:
    """Manages storage paths and access for project data."""

    PROJECTS_ROOT = "projects"

    # Define standard entity types and their file names
    PROJECT_BRIEF = "project_brief"
    PROJECT_LOG = "project_log"
    PROJECT_DASHBOARD = "project_dashboard"
    PROJECT_WHITEBOARD = "project_whiteboard"  # Changed from PROJECT_KB
    INFORMATION_REQUEST = "information_request"
    COORDINATOR_CONVERSATION = "coordinator_conversation"

    # Predefined entity types that have a single instance per project
    PREDEFINED_ENTITIES = {
        PROJECT_BRIEF: "brief.json",
        PROJECT_LOG: "log.json",
        PROJECT_DASHBOARD: "dashboard.json",
        PROJECT_WHITEBOARD: "whiteboard.json",  # Changed from kb.json
        COORDINATOR_CONVERSATION: "coordinator_conversation.json",
    }

    @staticmethod
    def get_projects_root() -> pathlib.Path:
        """Gets the root path for all projects."""
        return pathlib.Path(settings.storage.root) / ProjectStorageManager.PROJECTS_ROOT

    @staticmethod
    def get_project_dir(project_id: str) -> pathlib.Path:
        """Gets the directory for a specific project."""
        projects_root = ProjectStorageManager.get_projects_root()
        project_dir = projects_root / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir

    @staticmethod
    def get_shared_dir(project_id: str) -> pathlib.Path:
        """Gets the shared directory for a project."""
        project_dir = ProjectStorageManager.get_project_dir(project_id)
        shared_dir = project_dir / "shared"
        shared_dir.mkdir(parents=True, exist_ok=True)
        return shared_dir

    @staticmethod
    def get_entity_dir(project_id: str, entity_type: str) -> pathlib.Path:
        """Gets the directory for a specific entity type in the shared directory."""
        shared_dir = ProjectStorageManager.get_shared_dir(project_id)
        entity_dir = shared_dir / entity_type
        entity_dir.mkdir(parents=True, exist_ok=True)
        return entity_dir

    @staticmethod
    def get_conversation_dir(project_id: str, conversation_id: str, role: ProjectRole) -> pathlib.Path:
        """
        Gets the directory for a specific conversation within a project.

        Args:
            project_id: ID of the project
            conversation_id: ID of the conversation
            role: Role of the conversation (COORDINATOR or TEAM)

        Returns:
            Path to the conversation directory
        """
        project_dir = ProjectStorageManager.get_project_dir(project_id)

        # For Coordinator conversations, use the role as directory name
        if role == ProjectRole.COORDINATOR:
            conv_dir = project_dir / role.value
        else:
            # For team conversations, prefix the conversation ID with 'team_'
            conv_dir = project_dir / f"team_{conversation_id}"

        conv_dir.mkdir(parents=True, exist_ok=True)
        return conv_dir

    @staticmethod
    def get_brief_path(project_id: str) -> pathlib.Path:
        """Gets the path to the project brief file."""
        entity_dir = ProjectStorageManager.get_entity_dir(project_id, ProjectStorageManager.PROJECT_BRIEF)
        return entity_dir / ProjectStorageManager.PREDEFINED_ENTITIES[ProjectStorageManager.PROJECT_BRIEF]

    @staticmethod
    def get_project_log_path(project_id: str) -> pathlib.Path:
        """Gets the path to the project log file."""
        entity_dir = ProjectStorageManager.get_entity_dir(project_id, ProjectStorageManager.PROJECT_LOG)
        return entity_dir / ProjectStorageManager.PREDEFINED_ENTITIES[ProjectStorageManager.PROJECT_LOG]

    @staticmethod
    def get_project_dashboard_path(project_id: str) -> pathlib.Path:
        """Gets the path to the project dashboard file."""
        entity_dir = ProjectStorageManager.get_entity_dir(project_id, ProjectStorageManager.PROJECT_DASHBOARD)
        return entity_dir / ProjectStorageManager.PREDEFINED_ENTITIES[ProjectStorageManager.PROJECT_DASHBOARD]

    @staticmethod
    def get_project_whiteboard_path(project_id: str) -> pathlib.Path:
        """Gets the path to the project whiteboard file."""
        entity_dir = ProjectStorageManager.get_entity_dir(project_id, ProjectStorageManager.PROJECT_WHITEBOARD)
        return entity_dir / ProjectStorageManager.PREDEFINED_ENTITIES[ProjectStorageManager.PROJECT_WHITEBOARD]

    @staticmethod
    def get_coordinator_conversation_path(project_id: str) -> pathlib.Path:
        """Gets the path to the Coordinator conversation file."""
        entity_dir = ProjectStorageManager.get_entity_dir(project_id, ProjectStorageManager.COORDINATOR_CONVERSATION)
        return entity_dir / ProjectStorageManager.PREDEFINED_ENTITIES[ProjectStorageManager.COORDINATOR_CONVERSATION]

    @staticmethod
    def get_information_request_path(project_id: str, request_id: str) -> pathlib.Path:
        """Gets the path to an information request file."""
        entity_dir = ProjectStorageManager.get_entity_dir(project_id, ProjectStorageManager.INFORMATION_REQUEST)
        return entity_dir / f"{request_id}.json"

    @staticmethod
    def get_information_requests_dir(project_id: str) -> pathlib.Path:
        """Gets the directory containing all information requests."""
        return ProjectStorageManager.get_entity_dir(project_id, ProjectStorageManager.INFORMATION_REQUEST)

    @staticmethod
    def project_exists(project_id: str) -> bool:
        """Checks if a project exists."""
        project_dir = ProjectStorageManager.get_projects_root() / project_id
        return project_dir.exists()

    @staticmethod
    def get_conversation_role_file_path(context: ConversationContext) -> pathlib.Path:
        """Gets the path to the file that stores a conversation's role in projects."""
        storage_dir = storage_directory_for_context(context)
        storage_dir.mkdir(parents=True, exist_ok=True)
        return storage_dir / "project_role.json"

    @staticmethod
    def get_conversation_project_file_path(context: ConversationContext) -> pathlib.Path:
        """Gets the path to the file that stores a conversation's project association."""
        storage_dir = storage_directory_for_context(context)
        storage_dir.mkdir(parents=True, exist_ok=True)
        return storage_dir / "project_association.json"


class ProjectStorage:
    """Unified storage operations for project data."""

    @staticmethod
    def read_project_brief(project_id: str) -> Optional[ProjectBrief]:
        """Reads the project brief."""
        path = ProjectStorageManager.get_brief_path(project_id)
        return read_model(path, ProjectBrief)

    @staticmethod
    def write_project_brief(project_id: str, brief: ProjectBrief) -> pathlib.Path:
        """Writes the project brief."""
        path = ProjectStorageManager.get_brief_path(project_id)
        write_model(path, brief)
        return path

    @staticmethod
    def read_project_log(project_id: str) -> Optional[ProjectLog]:
        """Reads the project log."""
        path = ProjectStorageManager.get_project_log_path(project_id)
        return read_model(path, ProjectLog)

    @staticmethod
    def write_project_log(project_id: str, log: ProjectLog) -> pathlib.Path:
        """Writes the project log."""
        path = ProjectStorageManager.get_project_log_path(project_id)
        write_model(path, log)
        return path

    @staticmethod
    def read_project_dashboard(project_id: str) -> Optional[ProjectDashboard]:
        """Reads the project dashboard."""
        path = ProjectStorageManager.get_project_dashboard_path(project_id)
        return read_model(path, ProjectDashboard)

    @staticmethod
    def write_project_dashboard(project_id: str, dashboard: ProjectDashboard) -> pathlib.Path:
        """Writes the project dashboard."""
        path = ProjectStorageManager.get_project_dashboard_path(project_id)
        write_model(path, dashboard)
        return path

    @staticmethod
    def read_project_whiteboard(project_id: str) -> Optional[ProjectKB]:
        """Reads the project whiteboard."""
        path = ProjectStorageManager.get_project_whiteboard_path(project_id)
        return read_model(path, ProjectKB)

    @staticmethod
    def read_coordinator_conversation(project_id: str) -> Optional[CoordinatorConversationStorage]:
        """Reads the Coordinator conversation messages for a project."""
        path = ProjectStorageManager.get_coordinator_conversation_path(project_id)
        return read_model(path, CoordinatorConversationStorage)

    @staticmethod
    def write_coordinator_conversation(project_id: str, conversation: CoordinatorConversationStorage) -> pathlib.Path:
        """Writes the Coordinator conversation messages to storage."""
        path = ProjectStorageManager.get_coordinator_conversation_path(project_id)
        write_model(path, conversation)
        return path

    @staticmethod
    def append_coordinator_message(
        project_id: str,
        message_id: str,
        content: str,
        sender_name: str,
        is_assistant: bool = False,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Appends a message to the Coordinator conversation storage.

        Args:
            project_id: The ID of the project
            message_id: The ID of the message
            content: The message content
            sender_name: The name of the sender
            is_assistant: Whether the message is from the assistant
            timestamp: The timestamp of the message (defaults to now)
        """
        # Get existing conversation or create new one
        conversation = ProjectStorage.read_coordinator_conversation(project_id)
        if not conversation:
            conversation = CoordinatorConversationStorage(project_id=project_id)

        # Create new message
        new_message = CoordinatorConversationMessage(
            message_id=message_id,
            content=content,
            sender_name=sender_name,
            timestamp=timestamp or datetime.utcnow(),
            is_assistant=is_assistant,
        )

        # Add to conversation (only keep most recent 50 messages)
        conversation.messages.append(new_message)
        if len(conversation.messages) > 50:
            conversation.messages = conversation.messages[-50:]

        conversation.last_updated = datetime.utcnow()

        # Save the updated conversation
        ProjectStorage.write_coordinator_conversation(project_id, conversation)

    @staticmethod
    def write_project_whiteboard(project_id: str, kb: ProjectKB) -> pathlib.Path:
        """Writes the project whiteboard."""
        path = ProjectStorageManager.get_project_whiteboard_path(project_id)
        write_model(path, kb)
        return path

    @staticmethod
    def read_information_request(project_id: str, request_id: str) -> Optional[InformationRequest]:
        """Reads an information request."""
        path = ProjectStorageManager.get_information_request_path(project_id, request_id)
        return read_model(path, InformationRequest)

    @staticmethod
    def write_information_request(project_id: str, request: InformationRequest) -> pathlib.Path:
        """Writes an information request."""
        # Information requests must have an ID
        if not request.request_id:
            raise ValueError("Information request must have a request_id")

        path = ProjectStorageManager.get_information_request_path(project_id, request.request_id)
        write_model(path, request)
        return path

    @staticmethod
    def get_all_information_requests(project_id: str) -> List[InformationRequest]:
        """Gets all information requests for a project."""
        dir_path = ProjectStorageManager.get_information_requests_dir(project_id)
        requests = []

        if not dir_path.exists():
            return requests

        for file_path in dir_path.glob("*.json"):
            request = read_model(file_path, InformationRequest)
            if request:
                requests.append(request)

        # Sort by updated_at timestamp, newest first
        requests.sort(key=lambda r: r.updated_at, reverse=True)
        return requests

    @staticmethod
    async def refresh_current_ui(context: ConversationContext) -> None:
        """
        Refreshes only the current conversation's UI inspector panel.

        Use this when a change only affects the local conversation's view
        and doesn't need to be synchronized with other conversations.
        """
        from semantic_workbench_api_model.workbench_model import AssistantStateEvent

        # Create the state event
        state_event = AssistantStateEvent(
            state_id="project_status",  # Must match the inspector_state_providers key in chat.py
            event="updated",
            state=None,
        )

        # Send the event to the current context
        await context.send_conversation_state_event(state_event)

    @staticmethod
    async def refresh_all_project_uis(context: ConversationContext, project_id: str) -> None:
        """
        Refreshes the UI inspector panels of all conversations in a project.

        This sends a state event to all conversations (current, Coordinator, and all team members)
        involved in the project to refresh their inspector panels, ensuring all
        participants have the latest information without sending any text notifications.

        Use this when project data has changed and all UIs need to be updated,
        but you don't want to send notification messages to users.

        Args:
            context: Current conversation context
            project_id: The project ID
        """
        from semantic_workbench_api_model.workbench_model import AssistantStateEvent
        from .project import ConversationClientManager

        try:
            # First update the current conversation's UI
            await ProjectStorage.refresh_current_ui(context)

            # Get Coordinator client and update Coordinator if not the current conversation
            coordinator_client, coordinator_conversation_id = await ConversationClientManager.get_coordinator_client_for_project(
                context, project_id
            )
            if coordinator_client and coordinator_conversation_id:
                try:
                    state_event = AssistantStateEvent(state_id="project_status", event="updated", state=None)
                    # Get assistant ID from context
                    assistant_id = context.assistant.id
                    await coordinator_client.send_conversation_state_event(assistant_id, state_event)
                    logger.info(f"Sent state event to Coordinator conversation {coordinator_conversation_id} to refresh inspector")
                except Exception as e:
                    logger.warning(f"Error sending state event to Coordinator: {e}")

            # Get all team conversation clients and update them
            linked_conversations = await ConversationProjectManager.get_linked_conversations(context)
            current_id = str(context.id)

            for conv_id in linked_conversations:
                if conv_id != current_id and (not coordinator_conversation_id or conv_id != coordinator_conversation_id):
                    try:
                        # Get client for the conversation
                        client = ConversationClientManager.get_conversation_client(context, conv_id)

                        # Send state event to refresh the inspector panel
                        state_event = AssistantStateEvent(state_id="project_status", event="updated", state=None)
                        # Get assistant ID from context
                        assistant_id = context.assistant.id
                        await client.send_conversation_state_event(assistant_id, state_event)
                        logger.info(f"Sent state event to conversation {conv_id} to refresh inspector")
                    except Exception as e:
                        logger.warning(f"Error sending state event to conversation {conv_id}: {e}")
                        continue

        except Exception as e:
            logger.warning(f"Error notifying all project UIs: {e}")

    # The get_linked_conversations method is now in ConversationProjectManager

    @staticmethod
    async def log_project_event(
        context: ConversationContext,
        project_id: str,
        entry_type: str,
        message: str,
        related_entity_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Logs an event to the project log.

        Args:
            context: Current conversation context
            project_id: ID of the project
            entry_type: Type of log entry
            message: Log message
            related_entity_id: Optional ID of a related entity (e.g., information request)
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
        log = ProjectStorage.read_project_log(project_id)
        if not log:
            # Create a new project log
            log = ProjectLog(
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
        ProjectStorage.write_project_log(project_id, log)
        return True


class ProjectNotifier:
    """Handles notifications between conversations for project updates."""

    @staticmethod
    async def send_notice_to_linked_conversations(context: ConversationContext, project_id: str, message: str) -> None:
        """
        Sends a notice message to all linked conversations except the current one.
        Does NOT refresh any UI inspector panels.

        Args:
            context: Current conversation context
            project_id: ID of the project
            message: Notification message to send
        """
        from semantic_workbench_api_model.workbench_model import MessageType, NewConversationMessage
        from .project import ConversationClientManager

        # Get conversation IDs in the same project
        linked_conversations = await ConversationProjectManager.get_linked_conversations(context)
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
    async def notify_project_update(
        context: ConversationContext, project_id: str, update_type: str, message: str, 
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Complete project update: sends notices to all conversations and refreshes all UI inspector panels.

        This method:
        1. Sends a notice message to the current conversation
        2. Sends the same notice message to all linked conversations
        3. Refreshes UI inspector panels for all conversations in the project

        Use this for important project updates that need both user notification AND UI refresh.

        Args:
            context: Current conversation context
            project_id: ID of the project
            update_type: Type of update (e.g., 'brief', 'dashboard', 'information_request', etc.)
            message: Notification message to display to users
        """
        from semantic_workbench_api_model.workbench_model import MessageType, NewConversationMessage

        # Notify the current conversation with a message
        await context.send_messages(
            NewConversationMessage(
                content=message,
                message_type=MessageType.notice,
            )
        )

        # Notify all linked conversations with the same message
        await ProjectNotifier.send_notice_to_linked_conversations(context, project_id, message)

        # Refresh all project UI inspector panels
        await ProjectStorage.refresh_all_project_uis(context, project_id)


class ConversationProjectManager:
    """Manages the association between conversations and projects."""

    from pydantic import BaseModel, Field

    class ConversationRoleInfo(BaseModel):
        """Stores a conversation's role in a project."""

        project_id: str
        role: ProjectRole
        conversation_id: str

    class ProjectAssociation(BaseModel):
        """Stores a conversation's project association."""

        project_id: str

    @staticmethod
    async def get_linked_conversations(context: ConversationContext) -> List[str]:
        """
        Gets all conversations linked to this one through the same project.

        Args:
            context: Current conversation context

        Returns:
            List of conversation IDs that are part of the same project
        """
        try:
            # Get project ID
            project_id = await ConversationProjectManager.get_conversation_project(context)
            if not project_id:
                return []

            # Get all conversation role files in the storage
            project_dir = ProjectStorageManager.get_project_dir(project_id)
            if not project_dir.exists():
                return []

            # Look for conversation directories
            result = []
            conversation_id = str(context.id)

            # Check Coordinator directory
            coordinator_dir = project_dir / ProjectRole.COORDINATOR.value
            if coordinator_dir.exists():
                # If this isn't the current conversation, add it
                role_file = coordinator_dir / "conversation_role.json"
                if role_file.exists():
                    try:
                        role_data = read_model(role_file, ConversationProjectManager.ConversationRoleInfo)
                        if role_data and role_data.conversation_id != conversation_id:
                            result.append(role_data.conversation_id)
                    except Exception:
                        pass

            # Check team directories
            for team_dir in project_dir.glob("team_*"):
                if team_dir.is_dir():
                    # Extract conversation ID from directory name
                    team_id = team_dir.name[5:]  # Remove "team_" prefix
                    if team_id != conversation_id:
                        result.append(team_id)

            return result

        except Exception as e:
            logger.error(f"Error getting linked conversations: {e}")
            return []

    @staticmethod
    async def set_conversation_role(context: ConversationContext, project_id: str, role: ProjectRole) -> None:
        """
        Sets the role of a conversation in a project.

        Args:
            context: Conversation context
            project_id: ID of the project
            role: Role of the conversation (COORDINATOR or TEAM)
        """
        role_data = ConversationProjectManager.ConversationRoleInfo(
            project_id=project_id, role=role, conversation_id=str(context.id)
        )
        role_path = ProjectStorageManager.get_conversation_role_file_path(context)
        write_model(role_path, role_data)

    @staticmethod
    async def get_conversation_role(context: ConversationContext) -> Optional[ProjectRole]:
        """
        Gets the role of a conversation in a project.

        Args:
            context: Conversation context

        Returns:
            The role, or None if not associated with a project
        """
        role_path = ProjectStorageManager.get_conversation_role_file_path(context)
        role_data = read_model(role_path, ConversationProjectManager.ConversationRoleInfo)

        if role_data:
            return role_data.role

        return None

    @staticmethod
    async def associate_conversation_with_project(context: ConversationContext, project_id: str) -> None:
        """
        Associates a conversation with a project.

        Args:
            context: Conversation context
            project_id: ID of the project to associate with
        """
        project_data = ConversationProjectManager.ProjectAssociation(project_id=project_id)
        project_path = ProjectStorageManager.get_conversation_project_file_path(context)
        write_model(project_path, project_data)

    @staticmethod
    async def get_associated_project_id(context: ConversationContext) -> Optional[str]:
        """
        Gets the project ID associated with a conversation.

        Args:
            context: Conversation context

        Returns:
            The project ID, or None if not associated with a project
        """
        project_path = ProjectStorageManager.get_conversation_project_file_path(context)
        project_data = read_model(project_path, ConversationProjectManager.ProjectAssociation)

        if project_data:
            return project_data.project_id

        return None

    # Maintain backwards compatibility with existing code
    # These methods are deprecated and should be removed in a future update
    @staticmethod
    async def set_conversation_project(context: ConversationContext, project_id: str) -> None:
        """
        DEPRECATED: Use associate_conversation_with_project instead.

        Associates a conversation with a project.
        """
        await ConversationProjectManager.associate_conversation_with_project(context, project_id)

    @staticmethod
    async def get_conversation_project(context: ConversationContext) -> Optional[str]:
        """
        DEPRECATED: Use get_associated_project_id instead.

        Gets the project ID associated with a conversation.
        """
        return await ConversationProjectManager.get_associated_project_id(context)
