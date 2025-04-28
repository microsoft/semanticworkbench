"""
Project storage management module.

Provides direct access to project data with a clean, simple storage approach.
"""

import pathlib
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from semantic_workbench_api_model.workbench_model import AssistantStateEvent, MessageType, NewConversationMessage
from semantic_workbench_assistant import settings
from semantic_workbench_assistant.assistant_app import ConversationContext
from semantic_workbench_assistant.assistant_app.context import storage_directory_for_context
from semantic_workbench_assistant.storage import read_model, write_model

# Import inside functions to avoid circular imports
from .logging import logger
from .project_data import (
    InformationRequest,
    LogEntry,
    LogEntryType,
    ProjectBrief,
    ProjectInfo,
    ProjectLog,
    ProjectWhiteboard,
)
from .utils import get_current_user


class ConversationRole(str, Enum):
    """
    Enumeration of conversation roles in a project.

    This enum represents the role that a conversation plays in a project,
    either as a Coordinator (managing the project) or as a Team member
    (participating in the project).
    """

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

    # File names for project entities
    PROJECT_INFO_FILE = "project.json"
    PROJECT_BRIEF_FILE = "brief.json"
    PROJECT_LOG_FILE = "log.json"
    PROJECT_WHITEBOARD_FILE = "whiteboard.json"
    COORDINATOR_CONVERSATION_FILE = "coordinator_conversation.json"

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
    def get_linked_conversations_dir(project_id: str) -> pathlib.Path:
        """Gets the directory that tracks linked conversations for a project."""
        project_dir = ProjectStorageManager.get_project_dir(project_id)
        linked_dir = project_dir / "linked_conversations"
        linked_dir.mkdir(parents=True, exist_ok=True)
        return linked_dir

    @staticmethod
    def get_project_info_path(project_id: str) -> pathlib.Path:
        """Gets the path to the project info file."""
        project_dir = ProjectStorageManager.get_project_dir(project_id)
        return project_dir / ProjectStorageManager.PROJECT_INFO_FILE

    @staticmethod
    def get_brief_path(project_id: str) -> pathlib.Path:
        """Gets the path to the project brief file."""
        project_dir = ProjectStorageManager.get_project_dir(project_id)
        return project_dir / ProjectStorageManager.PROJECT_BRIEF_FILE

    @staticmethod
    def get_project_log_path(project_id: str) -> pathlib.Path:
        """Gets the path to the project log file."""
        project_dir = ProjectStorageManager.get_project_dir(project_id)
        return project_dir / ProjectStorageManager.PROJECT_LOG_FILE

    @staticmethod
    def get_project_whiteboard_path(project_id: str) -> pathlib.Path:
        """Gets the path to the project whiteboard file."""
        project_dir = ProjectStorageManager.get_project_dir(project_id)
        return project_dir / ProjectStorageManager.PROJECT_WHITEBOARD_FILE

    @staticmethod
    def get_coordinator_conversation_path(project_id: str) -> pathlib.Path:
        """Gets the path to the Coordinator conversation file."""
        project_dir = ProjectStorageManager.get_project_dir(project_id)
        return project_dir / ProjectStorageManager.COORDINATOR_CONVERSATION_FILE

    @staticmethod
    def get_information_requests_dir(project_id: str) -> pathlib.Path:
        """Gets the directory containing all information requests."""
        project_dir = ProjectStorageManager.get_project_dir(project_id)
        requests_dir = project_dir / "requests"
        requests_dir.mkdir(parents=True, exist_ok=True)
        return requests_dir

    @staticmethod
    def get_information_request_path(project_id: str, request_id: str) -> pathlib.Path:
        """Gets the path to an information request file."""
        requests_dir = ProjectStorageManager.get_information_requests_dir(project_id)
        return requests_dir / f"{request_id}.json"

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
        file_path = storage_dir / "project_association.json"
        logger.info(f"Project association file path: {file_path} (exists: {file_path.exists()})")
        logger.info(f"Storage directory: {storage_dir} (exists: {storage_dir.exists()})")
        return file_path


class ProjectStorage:
    """Unified storage operations for project data."""

    @staticmethod
    def read_project_info(project_id: str) -> Optional[ProjectInfo]:
        """Reads the project info."""
        path = ProjectStorageManager.get_project_info_path(project_id)
        return read_model(path, ProjectInfo)

    @staticmethod
    def write_project_info(project_id: str, info: ProjectInfo) -> pathlib.Path:
        """Writes the project info."""
        path = ProjectStorageManager.get_project_info_path(project_id)
        write_model(path, info)
        return path

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
    def read_project_whiteboard(project_id: str) -> Optional[ProjectWhiteboard]:
        """Reads the project whiteboard."""
        path = ProjectStorageManager.get_project_whiteboard_path(project_id)
        return read_model(path, ProjectWhiteboard)

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
    def write_project_whiteboard(project_id: str, whiteboard: ProjectWhiteboard) -> pathlib.Path:
        """Writes the project whiteboard."""
        path = ProjectStorageManager.get_project_whiteboard_path(project_id)
        write_model(path, whiteboard)
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
        Refreshes the UI inspector panels of all conversations in a project except the
        shareable team conversation template.

        There are three types of conversations in the system:
        1. Coordinator Conversation - The main conversation for the project owner
        2. Shareable Team Conversation Template - Only used to generate the share URL, never directly used by any user
        3. Team Conversation(s) - Individual conversations for each team member

        This sends a state event to all relevant conversations (Coordinator and all active team members)
        involved in the project to refresh their inspector panels, ensuring all
        participants have the latest information without sending any text notifications.

        The shareable team conversation template is excluded because no user will ever see it -
        it only exists to create the share URL that team members can use to join.

        Use this when project data has changed and all UIs need to be updated,
        but you don't want to send notification messages to users.

        Args:
            context: Current conversation context
            project_id: The project ID
        """
        # Import ConversationClientManager locally to avoid circular imports
        from .conversation_clients import ConversationClientManager

        try:
            # First update the current conversation's UI
            await ProjectStorage.refresh_current_ui(context)

            # Get the shareable team conversation ID from project info to exclude it
            shareable_conversation_id = None
            project_info = ProjectStorage.read_project_info(project_id)
            if project_info and project_info.team_conversation_id:
                shareable_conversation_id = project_info.team_conversation_id
                logger.info(f"Excluding shareable team conversation from UI updates: {shareable_conversation_id}")

            # Get Coordinator client and update Coordinator if not the current conversation
            (
                coordinator_client,
                coordinator_conversation_id,
            ) = await ConversationClientManager.get_coordinator_client_for_project(context, project_id)
            if coordinator_client and coordinator_conversation_id:
                try:
                    state_event = AssistantStateEvent(state_id="project_status", event="updated", state=None)
                    # Get assistant ID from context
                    assistant_id = context.assistant.id
                    await coordinator_client.send_conversation_state_event(assistant_id, state_event)
                    logger.info(
                        f"Sent state event to Coordinator conversation {coordinator_conversation_id} to refresh inspector"
                    )
                except Exception as e:
                    logger.warning(f"Error sending state event to Coordinator: {e}")

            # Get all team conversation clients and update them
            linked_conversations = await ConversationProjectManager.get_linked_conversations(context)
            current_id = str(context.id)

            for conv_id in linked_conversations:
                # Skip current conversation, coordinator conversation, and shareable conversation
                if (
                    conv_id != current_id
                    and (not coordinator_conversation_id or conv_id != coordinator_conversation_id)
                    and (not shareable_conversation_id or conv_id != shareable_conversation_id)
                ):
                    try:
                        # Get client for the conversation
                        client = ConversationClientManager.get_conversation_client(context, conv_id)

                        # Send state event to refresh the inspector panel
                        state_event = AssistantStateEvent(state_id="project_status", event="updated", state=None)
                        # Get assistant ID from context
                        assistant_id = context.assistant.id
                        await client.send_conversation_state_event(assistant_id, state_event)
                    except Exception as e:
                        logger.warning(f"Error sending state event to conversation {conv_id}: {e}")
                        continue
                elif conv_id == shareable_conversation_id:
                    logger.info(f"Skipping UI update for shareable conversation: {conv_id}")

        except Exception as e:
            logger.warning(f"Error notifying all project UIs: {e}")

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
            log = ProjectLog(
                entries=[],
            )

        # Add the entry and update metadata
        log.entries.append(entry)

        # Save the updated log
        ProjectStorage.write_project_log(project_id, log)
        return True


class ProjectNotifier:
    """Handles notifications between conversations for project updates."""

    @staticmethod
    async def send_notice_to_linked_conversations(context: ConversationContext, project_id: str, message: str) -> None:
        """
        Sends a notice message to all linked conversations except:
        1. The current conversation
        2. The shareable team conversation template (used only for creating the share URL)

        NOTE: The shareable team conversation is NEVER used directly by any user.
        It's just a template that gets copied when team members redeem the share URL
        to create their own individual team conversations. We exclude it from notifications
        because no one will ever see those notifications.

        This method does NOT refresh any UI inspector panels.

        Args:
            context: Current conversation context
            project_id: ID of the project
            message: Notification message to send
        """
        # Import ConversationClientManager locally to avoid circular imports
        from .conversation_clients import ConversationClientManager

        # Get conversation IDs in the same project
        linked_conversations = await ConversationProjectManager.get_linked_conversations(context)
        current_conversation_id = str(context.id)

        # Get the shareable team conversation ID from project info
        # This is the conversation created by the coordinator for sharing,
        # not an actual user conversation
        shareable_conversation_id = None
        project_info = ProjectStorage.read_project_info(project_id)
        if project_info and project_info.team_conversation_id:
            shareable_conversation_id = project_info.team_conversation_id
            logger.info(f"Excluding shareable team conversation from notifications: {shareable_conversation_id}")

        # Send notification to each linked conversation, excluding current and shareable conversation
        for conv_id in linked_conversations:
            # Skip current conversation and the shareable team conversation
            if conv_id != current_conversation_id and (
                not shareable_conversation_id or conv_id != shareable_conversation_id
            ):
                try:
                    # Get client for the target conversation
                    client = ConversationClientManager.get_conversation_client(context, conv_id)

                    # Send the notification
                    await client.send_messages(
                        NewConversationMessage(
                            content=message,
                            message_type=MessageType.notice,
                            metadata={
                                "debug": {
                                    "project_id": project_id,
                                    "message": message,
                                    "sender": str(context.id),
                                }
                            },
                        )
                    )
                    logger.info(f"Sent notification to conversation {conv_id}")
                except Exception as e:
                    logger.error(f"Failed to notify conversation {conv_id}: {e}")
            elif conv_id == shareable_conversation_id:
                logger.info(f"Skipping notification to shareable conversation: {conv_id}")
            elif conv_id == current_conversation_id:
                logger.debug(f"Skipping notification to current conversation: {conv_id}")

    @staticmethod
    async def notify_project_update(
        context: ConversationContext,
        project_id: str,
        update_type: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        send_notification: bool = True,  # Add parameter to control notifications
    ) -> None:
        """
        Complete project update: sends notices to all conversations and refreshes all UI inspector panels.

        This method:
        1. Sends a notice message to the current conversation (if send_notification=True)
        2. Sends the same notice message to all linked conversations (if send_notification=True)
        3. Refreshes UI inspector panels for all conversations in the project

        Use this for important project updates that need both user notification AND UI refresh.
        Set send_notification=False for frequent updates (like file syncs, whiteboard updates) to
        avoid notification spam.

        Args:
            context: Current conversation context
            project_id: ID of the project
            update_type: Type of update (e.g., 'brief', 'project_info', 'information_request', etc.)
            message: Notification message to display to users
            data: Optional additional data related to the update
            send_notification: Whether to send notifications (default: True)
        """

        # Only send notifications if explicitly requested
        if send_notification:
            # Notify all linked conversations with the same message
            await ProjectNotifier.send_notice_to_linked_conversations(context, project_id, message)

        # Always refresh all project UI inspector panels to keep UI in sync
        # This will update the UI without sending notifications
        await ProjectStorage.refresh_all_project_uis(context, project_id)


class ConversationProjectManager:
    """Manages the association between conversations and projects."""

    class ConversationRoleInfo(BaseModel):
        """Stores a conversation's role in a project."""

        project_id: str
        role: ConversationRole
        conversation_id: str

    class ProjectAssociation(BaseModel):
        """Stores a conversation's project association."""

        project_id: str

    @staticmethod
    async def get_linked_conversations(context: ConversationContext) -> List[str]:
        """
        Gets all conversations linked to this one through the same project.
        """
        try:
            # Get project ID
            project_id = await ConversationProjectManager.get_associated_project_id(context)
            if not project_id:
                return []

            # Get the linked conversations directory
            linked_dir = ProjectStorageManager.get_linked_conversations_dir(project_id)
            if not linked_dir.exists():
                return []

            # Get all conversation files in the directory
            result = []
            conversation_id = str(context.id)

            # Each file in the directory represents a linked conversation
            # The filename itself is the conversation ID
            for file_path in linked_dir.glob("*"):
                if file_path.is_file():
                    # The filename is the conversation ID
                    conv_id = file_path.name
                    if conv_id != conversation_id:
                        result.append(conv_id)

            return result

        except Exception as e:
            logger.error(f"Error getting linked conversations: {e}")
            return []

    @staticmethod
    async def set_conversation_role(context: ConversationContext, project_id: str, role: ConversationRole) -> None:
        """
        Sets the role of a conversation in a project.
        """
        role_data = ConversationProjectManager.ConversationRoleInfo(
            project_id=project_id, role=role, conversation_id=str(context.id)
        )
        role_path = ProjectStorageManager.get_conversation_role_file_path(context)
        write_model(role_path, role_data)

    @staticmethod
    async def get_conversation_role(context: ConversationContext) -> Optional[ConversationRole]:
        """
        Gets the role of a conversation in a project.
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
        """
        logger.info(f"Associating conversation {context.id} with project {project_id}")

        try:
            # 1. Store the project association in the conversation's storage directory
            project_data = ConversationProjectManager.ProjectAssociation(project_id=project_id)
            project_path = ProjectStorageManager.get_conversation_project_file_path(context)
            logger.info(f"Writing project association to {project_path}")
            write_model(project_path, project_data)

            # 2. Register this conversation in the project's linked_conversations directory
            linked_dir = ProjectStorageManager.get_linked_conversations_dir(project_id)
            logger.info(f"Registering in linked_conversations directory: {linked_dir}")
            conversation_file = linked_dir / str(context.id)

            # Touch the file to create it if it doesn't exist
            # We don't need to write any content to it, just its existence is sufficient
            conversation_file.touch(exist_ok=True)
            logger.info(f"Created conversation link file: {conversation_file}")
        except Exception as e:
            logger.error(f"Error associating conversation with project: {e}")
            raise

    @staticmethod
    async def get_associated_project_id(context: ConversationContext) -> Optional[str]:
        """
        Gets the project ID associated with a conversation.
        """
        project_path = ProjectStorageManager.get_conversation_project_file_path(context)
        project_data = read_model(project_path, ConversationProjectManager.ProjectAssociation)

        if project_data:
            return project_data.project_id

        return None
