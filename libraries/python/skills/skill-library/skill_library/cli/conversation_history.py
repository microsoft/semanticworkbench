import datetime
import uuid
from typing import Any, Dict, List, Optional

from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    ConversationMessageList,
    MessageSender,
    ParticipantRole,
)
from skill_library.cli.skill_logger import SkillLogger


class ConversationHistory:
    """Manages conversation history for routine execution."""

    def __init__(self, logger: SkillLogger):
        self.messages = []
        self.logger = logger

    def add_message(
        self,
        content: str,
        sender_role: ParticipantRole,
        message_type: str = "chat",
        content_type: str = "text/plain",
        filenames: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a message to the conversation history."""
        sender = MessageSender(participant_role=sender_role, participant_id=f"{sender_role}-cli")

        msg_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now().isoformat()

        self.messages.append({
            "id": msg_id,
            "sender": sender,
            "message_type": message_type,
            "timestamp": timestamp,
            "content_type": content_type,
            "content": content,
            "filenames": filenames or [],
            "metadata": metadata or {},
            "has_debug_data": False,
        })

        # Log the message addition
        short_content = content[:50] + "..." if len(content) > 50 else content
        self.logger.debug(
            f"Added message from {sender_role}: {short_content}",
            {"message_id": msg_id, "sender_role": str(sender_role)},
        )

    async def get_message_list(self) -> ConversationMessageList:
        """Convert history to ConversationMessageList format."""
        result = []
        for msg_dict in self.messages:
            # Deep copy to avoid modifying the original
            msg_copy = dict(msg_dict)

            # Convert ID from string to UUID
            msg_copy["id"] = uuid.UUID(msg_copy["id"])

            # Convert timestamp from string to datetime
            msg_copy["timestamp"] = datetime.datetime.fromisoformat(msg_copy["timestamp"])

            # Create ConversationMessage object
            result.append(ConversationMessage(**msg_copy))

        return ConversationMessageList(messages=result)

    def display_history(self):
        """Display conversation history."""
        self.logger.info("\nConversation History:")
        for i, msg in enumerate(self.messages):
            role = msg["sender"]["participant_role"]
            timestamp = datetime.datetime.fromisoformat(msg["timestamp"]).strftime("%H:%M:%S")
            content = msg["content"]
            # Truncate long messages
            if len(content) > 80:
                content = content[:77] + "..."
            self.logger.info(f"  [{timestamp}] {role}: {content}")
