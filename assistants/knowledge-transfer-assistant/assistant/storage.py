"""
KnowledgePackage storage management module.

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
from .data import (
    InformationRequest,
    KnowledgeBrief,
    KnowledgeDigest,
    KnowledgePackage,
    KnowledgePackageLog,
    LogEntry,
    LogEntryType,
)
from .storage_models import CoordinatorConversationMessage, CoordinatorConversationStorage
from .utils import get_current_user


class ShareStorageManager:
    """Manages storage paths and access for project data."""

    SHARES_ROOT = "shares"

    # File names for project entities
    SHARE_INFO_FILE = "share.json"  # Legacy file, kept for backward compatibility
    SHARE_LOG_FILE = "log.json"  # Separate log file
    COORDINATOR_CONVERSATION_FILE = "coordinator_conversation.json"  # Separate conversation file
    SHARE_FILE = "share_data.json"  # Main consolidated data file
    
    # Deprecated file names (no longer used but kept for reference)
    SHARE_BRIEF_FILE = "brief.json"  # Now stored in SHARE_FILE
    SHARE_KNOWLEDGE_DIGEST_FILE = "knowledge_digest.json"  # Now stored in SHARE_FILE

    @staticmethod
    def get_shares_root() -> pathlib.Path:
        """Gets the root path for all projects."""
        return pathlib.Path(settings.storage.root) / ShareStorageManager.SHARES_ROOT

    @staticmethod
    def get_share_dir(share_id: str) -> pathlib.Path:
        """Gets the directory for a specific project."""
        shares_root = ShareStorageManager.get_shares_root()
        share_dir = shares_root / share_id
        share_dir.mkdir(parents=True, exist_ok=True)
        return share_dir

    @staticmethod
    def get_linked_conversations_dir(share_id: str) -> pathlib.Path:
        """Gets the directory that tracks linked conversations for a project."""
        share_dir = ShareStorageManager.get_share_dir(share_id)
        linked_dir = share_dir / "linked_conversations"
        linked_dir.mkdir(parents=True, exist_ok=True)
        return linked_dir

    @staticmethod
    def get_share_info_path(share_id: str) -> pathlib.Path:
        """Gets the path to the project info file."""
        share_dir = ShareStorageManager.get_share_dir(share_id)
        return share_dir / ShareStorageManager.SHARE_INFO_FILE

    @staticmethod
    def get_brief_path(share_id: str) -> pathlib.Path:
        """Gets the path to the project brief file (deprecated - brief now stored in main share file)."""
        share_dir = ShareStorageManager.get_share_dir(share_id)
        return share_dir / ShareStorageManager.SHARE_BRIEF_FILE

    @staticmethod
    def get_share_log_path(share_id: str) -> pathlib.Path:
        """Gets the path to the project log file."""
        share_dir = ShareStorageManager.get_share_dir(share_id)
        return share_dir / ShareStorageManager.SHARE_LOG_FILE

    @staticmethod
    def get_knowledge_digest_path(share_id: str) -> pathlib.Path:
        """Gets the path to the knowledge digest file (deprecated - digest now stored in main share file)."""
        share_dir = ShareStorageManager.get_share_dir(share_id)
        return share_dir / ShareStorageManager.SHARE_KNOWLEDGE_DIGEST_FILE

    @staticmethod
    def get_coordinator_conversation_path(share_id: str) -> pathlib.Path:
        """Gets the path to the Coordinator conversation file."""
        share_dir = ShareStorageManager.get_share_dir(share_id)
        return share_dir / ShareStorageManager.COORDINATOR_CONVERSATION_FILE

    @staticmethod
    def get_share_path(share_id: str) -> pathlib.Path:
        """Gets the path to the complete KnowledgePackage data file."""
        share_dir = ShareStorageManager.get_share_dir(share_id)
        return share_dir / ShareStorageManager.SHARE_FILE

    @staticmethod
    def get_information_requests_dir(share_id: str) -> pathlib.Path:
        """Gets the directory containing all information requests (deprecated - requests now stored in main share file)."""
        share_dir = ShareStorageManager.get_share_dir(share_id)
        requests_dir = share_dir / "requests"
        requests_dir.mkdir(parents=True, exist_ok=True)
        return requests_dir

    @staticmethod
    def get_information_request_path(share_id: str, request_id: str) -> pathlib.Path:
        """Gets the path to an information request file (deprecated - requests now stored in main share file)."""
        requests_dir = ShareStorageManager.get_information_requests_dir(share_id)
        return requests_dir / f"{request_id}.json"

    @staticmethod
    def share_exists(share_id: str) -> bool:
        """Checks if a project exists."""
        share_dir = ShareStorageManager.get_shares_root() / share_id
        return share_dir.exists()

    @staticmethod
    def get_conversation_role_file_path(context: ConversationContext) -> pathlib.Path:
        """Gets the path to the file that stores a conversation's role in projects."""
        storage_dir = storage_directory_for_context(context)
        storage_dir.mkdir(parents=True, exist_ok=True)
        return storage_dir / "share_role.json"

    @staticmethod
    def get_conversation_share_file_path(context: ConversationContext) -> pathlib.Path:
        """Gets the path to the file that stores a conversation's project association."""
        storage_dir = storage_directory_for_context(context)
        storage_dir.mkdir(parents=True, exist_ok=True)
        file_path = storage_dir / "share_association.json"
        return file_path


class ShareStorage:
    """Unified storage operations for project data."""

    @staticmethod
    def read_share_info(share_id: str) -> Optional[KnowledgePackage]:
        """Reads the knowledge package (deprecated, use read_share instead)."""
        return ShareStorage.read_share(share_id)

    @staticmethod
    def write_share_info(share_id: str, package: KnowledgePackage) -> pathlib.Path:
        """Writes the knowledge package (deprecated, use write_share instead)."""
        return ShareStorage.write_share(share_id, package)

    @staticmethod
    def read_knowledge_brief(share_id: str) -> Optional[KnowledgeBrief]:
        """Reads the knowledge brief from the main share data."""
        package = ShareStorage.read_share(share_id)
        return package.brief if package else None

    @staticmethod
    def write_knowledge_brief(share_id: str, brief: KnowledgeBrief) -> pathlib.Path:
        """Writes the knowledge brief to the main share data."""
        package = ShareStorage.read_share(share_id)
        if not package:
            # Create a new package if it doesn't exist
            package = KnowledgePackage(
                share_id=share_id,
                brief=brief,
                digest=None,
            )
        else:
            package.brief = brief
        
        return ShareStorage.write_share(share_id, package)

    @staticmethod
    def read_share_log(share_id: str) -> Optional[KnowledgePackageLog]:
        """Reads the project log."""
        path = ShareStorageManager.get_share_log_path(share_id)
        return read_model(path, KnowledgePackageLog)

    @staticmethod
    def write_share_log(share_id: str, log: KnowledgePackageLog) -> pathlib.Path:
        """Writes the project log."""
        path = ShareStorageManager.get_share_log_path(share_id)
        write_model(path, log)
        return path

    @staticmethod
    def read_knowledge_digest(share_id: str) -> Optional[KnowledgeDigest]:
        """Reads the knowledge digest from the main share data."""
        package = ShareStorage.read_share(share_id)
        return package.digest if package else None

    @staticmethod
    def read_coordinator_conversation(share_id: str) -> Optional[CoordinatorConversationStorage]:
        """Reads the Coordinator conversation messages for a project."""
        path = ShareStorageManager.get_coordinator_conversation_path(share_id)
        return read_model(path, CoordinatorConversationStorage)

    @staticmethod
    def write_coordinator_conversation(share_id: str, conversation: CoordinatorConversationStorage) -> pathlib.Path:
        """Writes the Coordinator conversation messages to storage."""
        path = ShareStorageManager.get_coordinator_conversation_path(share_id)
        write_model(path, conversation)
        return path

    @staticmethod
    def append_coordinator_message(
        share_id: str,
        message_id: str,
        content: str,
        sender_name: str,
        is_assistant: bool = False,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Appends a message to the Coordinator conversation storage.

        Args:
            share_id: The ID of the project
            message_id: The ID of the message
            content: The message content
            sender_name: The name of the sender
            is_assistant: Whether the message is from the assistant
            timestamp: The timestamp of the message (defaults to now)
        """
        # Get existing conversation or create new one
        conversation = ShareStorage.read_coordinator_conversation(share_id)
        if not conversation:
            conversation = CoordinatorConversationStorage(knowledge_share_id=share_id)

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
        ShareStorage.write_coordinator_conversation(share_id, conversation)

    @staticmethod
    def write_share_whiteboard(share_id: str, digest: KnowledgeDigest) -> pathlib.Path:
        """Writes the knowledge digest (deprecated method name for backward compatibility)."""
        return ShareStorage.write_knowledge_digest(share_id, digest)

    @staticmethod
    def write_knowledge_digest(share_id: str, digest: KnowledgeDigest) -> pathlib.Path:
        """Writes the knowledge digest to the main share data."""
        package = ShareStorage.read_share(share_id)
        if not package:
            # Create a new package if it doesn't exist
            package = KnowledgePackage(
                share_id=share_id,
                brief=None,
                digest=digest,
            )
        else:
            package.digest = digest
        
        return ShareStorage.write_share(share_id, package)

    @staticmethod
    def read_information_request(share_id: str, request_id: str) -> Optional[InformationRequest]:
        """Reads an information request from the main share data."""
        package = ShareStorage.read_share(share_id)
        if not package or not package.requests:
            return None
        
        for request in package.requests:
            if request.request_id == request_id:
                return request
        
        return None

    @staticmethod
    def write_information_request(share_id: str, request: InformationRequest) -> pathlib.Path:
        """Writes an information request to the main share data."""
        # Information requests must have an ID
        if not request.request_id:
            raise ValueError("Information request must have a request_id")

        package = ShareStorage.read_share(share_id)
        if not package:
            # Create a new package if it doesn't exist
            package = KnowledgePackage(
                share_id=share_id,
                brief=None,
                digest=None,
                requests=[request],
            )
        else:
            # Update existing request or add new one
            existing_requests = package.requests or []
            updated = False
            for i, existing_request in enumerate(existing_requests):
                if existing_request.request_id == request.request_id:
                    existing_requests[i] = request
                    updated = True
                    break
            
            if not updated:
                existing_requests.append(request)
            
            package.requests = existing_requests
        
        return ShareStorage.write_share(share_id, package)

    @staticmethod
    def read_share(share_id: str) -> Optional[KnowledgePackage]:
        """Reads the complete KnowledgePackage data."""
        path = ShareStorageManager.get_share_path(share_id)
        return read_model(path, KnowledgePackage)

    @staticmethod
    def write_share(share_id: str, project: KnowledgePackage) -> pathlib.Path:
        """Writes the complete KnowledgePackage data."""
        path = ShareStorageManager.get_share_path(share_id)
        write_model(path, project)
        return path

    @staticmethod
    def get_all_information_requests(share_id: str) -> List[InformationRequest]:
        """Gets all information requests from the main share data."""
        package = ShareStorage.read_share(share_id)
        if not package:
            return []
        
        # Sort by updated_at timestamp, newest first
        requests = package.requests or []
        requests.sort(key=lambda r: r.updated_at, reverse=True)
        return requests

    @staticmethod
    async def refresh_current_ui(context: ConversationContext) -> None:
        """
        Refreshes only the current conversation's UI inspector panel.

        This function is now a wrapper that calls the implementation in project_notifications.py.
        """
        from .notifications import refresh_current_ui

        await refresh_current_ui(context)

    @staticmethod
    async def refresh_all_share_uis(context: ConversationContext, share_id: str) -> None:
        """
        Refreshes the UI inspector panels of all conversations in a project.

        This function is now a wrapper that calls the implementation in project_notifications.py.
        """
        from .notifications import refresh_all_project_uis

        await refresh_all_project_uis(context, share_id)

    @staticmethod
    async def log_share_event(
        context: ConversationContext,
        share_id: str,
        entry_type: str,
        message: str,
        related_entity_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Logs an event to the project log.

        Args:
            context: Current conversation context
            share_id: ID of the project
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
        log = ShareStorage.read_share_log(share_id)
        if not log:
            log = KnowledgePackageLog(
                entries=[],
            )

        # Add the entry and update metadata
        log.entries.append(entry)

        # Save the updated log
        ShareStorage.write_share_log(share_id, log)
        return True
