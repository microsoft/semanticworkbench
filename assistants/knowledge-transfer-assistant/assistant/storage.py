"""
KnowledgePackage storage management module.

Provides direct access to knowledge transfer data with a clean, simple storage approach.
"""

import pathlib
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .data import InspectorTab

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
from .data import CoordinatorConversationMessage, CoordinatorConversationMessages
from .utils import get_current_user


class ShareStorageManager:
    """Manages storage paths and access for knowledge transfer data."""

    SHARES_ROOT = "shares"

    # File names for knowledge transfer entities
    SHARE_LOG_FILE = "log.json"
    COORDINATOR_CONVERSATION_FILE = "coordinator_conversation.json"
    SHARE_FILE = "share_data.json"  # Main consolidated data file

    @staticmethod
    def get_shares_root() -> pathlib.Path:
        """Gets the root path for all shares."""
        return pathlib.Path(settings.storage.root) / ShareStorageManager.SHARES_ROOT

    @staticmethod
    def get_share_dir(share_id: str) -> pathlib.Path:
        """Gets the directory for a specific share."""
        shares_root = ShareStorageManager.get_shares_root()
        share_dir = shares_root / share_id
        share_dir.mkdir(parents=True, exist_ok=True)
        return share_dir

    @staticmethod
    def get_share_log_path(share_id: str) -> pathlib.Path:
        """Gets the path to the knowledge transfer log file."""
        share_dir = ShareStorageManager.get_share_dir(share_id)
        return share_dir / ShareStorageManager.SHARE_LOG_FILE

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
    def share_exists(share_id: str) -> bool:
        """Checks if a share exists."""
        share_dir = ShareStorageManager.get_shares_root() / share_id
        return share_dir.exists()

    @staticmethod
    def get_conversation_role_file_path(context: ConversationContext) -> pathlib.Path:
        """Gets the path to the file that stores a conversation's role in the share."""
        storage_dir = storage_directory_for_context(context)
        storage_dir.mkdir(parents=True, exist_ok=True)
        return storage_dir / "share_role.json"

class ShareStorage:
    """Unified storage operations for knowledge transfer share data."""

    @staticmethod
    def read_share(share_id: str) -> Optional[KnowledgePackage]:
        """Reads the complete KnowledgePackage data."""
        path = ShareStorageManager.get_share_path(share_id)
        return read_model(path, KnowledgePackage)

    @staticmethod
    def write_share(share_id: str, package: KnowledgePackage) -> pathlib.Path:
        """Writes the complete KnowledgePackage data."""
        path = ShareStorageManager.get_share_path(share_id)
        write_model(path, package)
        return path

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
        path = ShareStorageManager.get_share_log_path(share_id)
        return read_model(path, KnowledgePackageLog)

    @staticmethod
    def write_share_log(share_id: str, log: KnowledgePackageLog) -> pathlib.Path:
        path = ShareStorageManager.get_share_log_path(share_id)
        write_model(path, log)
        return path

    @staticmethod
    def read_knowledge_digest(share_id: str) -> Optional[KnowledgeDigest]:
        package = ShareStorage.read_share(share_id)
        return package.digest if package else None

    @staticmethod
    def read_coordinator_conversation(share_id: str) -> Optional[CoordinatorConversationMessages]:
        path = ShareStorageManager.get_coordinator_conversation_path(share_id)
        return read_model(path, CoordinatorConversationMessages)

    @staticmethod
    def write_coordinator_conversation(share_id: str, conversation: CoordinatorConversationMessages) -> pathlib.Path:
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
            share_id: The ID of the share
            message_id: The ID of the message
            content: The message content
            sender_name: The name of the sender
            is_assistant: Whether the message is from the assistant
            timestamp: The timestamp of the message (defaults to now)
        """
        conversation = ShareStorage.read_coordinator_conversation(share_id)
        if not conversation:
            conversation = CoordinatorConversationMessages(knowledge_share_id=share_id)

        new_message = CoordinatorConversationMessage(
            message_id=message_id,
            content=content,
            sender_name=sender_name,
            timestamp=timestamp or datetime.utcnow(),
            is_assistant=is_assistant,
        )

        conversation.messages.append(new_message)
        if len(conversation.messages) > 50:
            conversation.messages = conversation.messages[-50:]

        conversation.last_updated = datetime.utcnow()

        ShareStorage.write_coordinator_conversation(share_id, conversation)

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
    async def refresh_all_share_uis(context: ConversationContext, share_id: str, tabs: List["InspectorTab"]) -> None:
        """
        Refreshes the UI inspector panels of all conversations in a knowledge transfer.
        Args:
            context: Current conversation context
            share_id: The share ID
            tabs: List of InspectorTab values to update. If None, updates all tabs.
        """

        from .notifications import Notifications

        await Notifications.notify_all_state_update(context, share_id, tabs)

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
        Logs an event to the knowledge transfer log.

        Args:
            context: Current conversation context
            share_id: ID of the share
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
