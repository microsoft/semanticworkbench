import pathlib
from datetime import datetime
from typing import Any

from semantic_workbench_assistant import settings
from semantic_workbench_assistant.assistant_app import ConversationContext
from semantic_workbench_assistant.assistant_app.context import (
    storage_directory_for_context,
)
from semantic_workbench_assistant.storage import read_model, write_model

from assistant.errors import NoShareException
from assistant.logging import logger

# Import inside functions to avoid circular imports
from .data import (
    ConversationPreferences,
    CoordinatorConversationMessage,
    CoordinatorConversationMessages,
    InformationRequest,
    KnowledgeBrief,
    KnowledgeDigest,
    LogEntry,
    LogEntryType,
    Share,
    ShareLog,
)
from .utils import get_current_user


class ShareStorageManager:
    """Manages storage paths and access for knowledge transfer data."""

    SHARES_ROOT = "shares"
    SHARE_LOG_FILE = "log.json"
    COORDINATOR_CONVERSATION_FILE = "coordinator_conversation.json"
    SHARE_FILE = "share_data.json"

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
        """Gets the path to the complete data file."""
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


class ConversationStorage:
    @staticmethod
    def get_conversation_preferences_file_path(context: ConversationContext) -> pathlib.Path:
        """Gets the path to the file that stores conversation preferences."""
        storage_dir = storage_directory_for_context(context)
        storage_dir.mkdir(parents=True, exist_ok=True)
        return storage_dir / "conversation_preferences.json"

    @staticmethod
    def read_conversation_preferences(context: ConversationContext) -> ConversationPreferences | None:
        path = ConversationStorage.get_conversation_preferences_file_path(context)
        return read_model(path, ConversationPreferences)

    @staticmethod
    def write_conversation_preferences(context: ConversationContext, preferences: ConversationPreferences) -> None:
        path = ConversationStorage.get_conversation_preferences_file_path(context)
        write_model(path, preferences)


class ShareStorage:
    @staticmethod
    def read_share(share_id: str) -> Share | None:
        path = ShareStorageManager.get_share_path(share_id)
        return read_model(path, Share)

    @staticmethod
    def write_share(share_id: str, share: Share) -> pathlib.Path:
        path = ShareStorageManager.get_share_path(share_id)
        write_model(path, share)
        return path

    @staticmethod
    def read_assistant_thoughts(share_id: str) -> list[str]:
        share = ShareStorage.read_share(share_id)
        if not share:
            return []
        return share.assistant_thoughts

    @staticmethod
    def add_assistant_thoughts(share_id: str, thoughts: list[str]) -> None:
        share = ShareStorage.read_share(share_id)
        if not share:
            raise NoShareException
        share.assistant_thoughts.extend(thoughts)
        ShareStorage.write_share(share_id, share)

    @staticmethod
    def remove_assistant_thought(share_id: str, thought: str) -> None:
        share = ShareStorage.read_share(share_id)
        if not share:
            raise NoShareException
        if thought in share.assistant_thoughts:
            share.assistant_thoughts.remove(thought)
            ShareStorage.write_share(share_id, share)
        else:
            logger.warning(f"Thought '{thought}' not found in share {share_id}.")

    @staticmethod
    def read_knowledge_brief(share_id: str) -> KnowledgeBrief | None:
        share = ShareStorage.read_share(share_id)
        return share.brief if share else None

    @staticmethod
    def write_knowledge_brief(share_id: str, brief: KnowledgeBrief) -> pathlib.Path:
        share = ShareStorage.read_share(share_id)
        if not share:
            raise NoShareException
        share.brief = brief
        return ShareStorage.write_share(share_id, share)

    @staticmethod
    def read_share_log(share_id: str) -> ShareLog | None:
        path = ShareStorageManager.get_share_log_path(share_id)
        return read_model(path, ShareLog)

    @staticmethod
    def write_share_log(share_id: str, log: ShareLog) -> pathlib.Path:
        path = ShareStorageManager.get_share_log_path(share_id)
        write_model(path, log)
        return path

    @staticmethod
    def read_knowledge_digest(share_id: str) -> KnowledgeDigest | None:
        share = ShareStorage.read_share(share_id)
        return share.digest if share else None

    @staticmethod
    def read_coordinator_conversation(
        share_id: str,
    ) -> CoordinatorConversationMessages | None:
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
        timestamp: datetime | None = None,
    ) -> None:
        """
        Appends a message to the Coordinator conversation storage.
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
        share = ShareStorage.read_share(share_id)
        if not share:
            raise NoShareException
        share.digest = digest
        return ShareStorage.write_share(share_id, share)

    @staticmethod
    def read_information_request(share_id: str, request_id: str) -> InformationRequest | None:
        share = ShareStorage.read_share(share_id)
        if not share:
            raise NoShareException
        if not share.requests:
            return None
        for request in share.requests:
            if request.request_id == request_id:
                return request
        return None

    @staticmethod
    def write_information_request(share_id: str, request: InformationRequest) -> pathlib.Path:
        # Information requests must have an ID
        if not request.request_id:
            raise ValueError("Information request must have a request_id")
        share = ShareStorage.read_share(share_id)
        if not share:
            raise NoShareException

        # Update existing request or add new one
        existing_requests = share.requests or []
        updated = False
        for i, existing_request in enumerate(existing_requests):
            if existing_request.request_id == request.request_id:
                existing_requests[i] = request
                updated = True
                break
        if not updated:
            existing_requests.append(request)

        share.requests = existing_requests
        return ShareStorage.write_share(share_id, share)

    @staticmethod
    def get_all_information_requests(share_id: str) -> list[InformationRequest]:
        share = ShareStorage.read_share(share_id)
        if not share:
            return []

        # Sort by updated_at timestamp, newest first
        requests = share.requests or []
        requests.sort(key=lambda r: r.updated_at, reverse=True)
        return requests

    @staticmethod
    async def log_share_event(
        context: ConversationContext,
        share_id: str,
        entry_type: str,
        message: str,
        related_entity_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Logs an event to the log.

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
        user_id, user_name = await get_current_user(context)
        if not user_id:
            return

        entry = LogEntry(
            entry_type=LogEntryType(entry_type),
            message=message,
            user_id=user_id,
            user_name=user_name or "Unknown User",
            related_entity_id=related_entity_id,
            metadata=metadata or {},
        )

        try:
            log = ShareStorage.read_share_log(share_id)
            if not log:
                log = ShareLog(
                    entries=[],
                )
            log.entries.append(entry)
            ShareStorage.write_share_log(share_id, log)
        except Exception as e:
            logger.exception(
                f"Failed to log share event for share {share_id}: {e}",
                exc_info=True,
            )
            return
        return
