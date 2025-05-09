"""
Project storage management module.

Provides direct access to project data with a clean, simple storage approach.
"""

import pathlib
from datetime import datetime
from typing import Any, Dict, List, Optional

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
    Project,
    ProjectBrief,
    ProjectInfo,
    ProjectLog,
    ProjectWhiteboard,
)
from .project_storage_models import CoordinatorConversationMessage, CoordinatorConversationStorage
from .utils import get_current_user


class ProjectStorageManager:
    """Manages storage paths and access for project data."""

    PROJECTS_ROOT = "projects"

    # File names for project entities
    PROJECT_INFO_FILE = "project.json"
    PROJECT_BRIEF_FILE = "brief.json"
    PROJECT_LOG_FILE = "log.json"
    PROJECT_WHITEBOARD_FILE = "whiteboard.json"
    COORDINATOR_CONVERSATION_FILE = "coordinator_conversation.json"
    PROJECT_FILE = "project_data.json"

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
    def get_project_path(project_id: str) -> pathlib.Path:
        """Gets the path to the complete Project data file."""
        project_dir = ProjectStorageManager.get_project_dir(project_id)
        return project_dir / ProjectStorageManager.PROJECT_FILE

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
    def read_project(project_id: str) -> Optional[Project]:
        """Reads the complete Project data."""
        path = ProjectStorageManager.get_project_path(project_id)
        return read_model(path, Project)

    @staticmethod
    def write_project(project_id: str, project: Project) -> pathlib.Path:
        """Writes the complete Project data."""
        path = ProjectStorageManager.get_project_path(project_id)
        write_model(path, project)
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

        This function is now a wrapper that calls the implementation in project_notifications.py.
        """
        from .project_notifications import refresh_current_ui

        await refresh_current_ui(context)

    @staticmethod
    async def refresh_all_project_uis(context: ConversationContext, project_id: str) -> None:
        """
        Refreshes the UI inspector panels of all conversations in a project.

        This function is now a wrapper that calls the implementation in project_notifications.py.
        """
        from .project_notifications import refresh_all_project_uis

        await refresh_all_project_uis(context, project_id)

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
