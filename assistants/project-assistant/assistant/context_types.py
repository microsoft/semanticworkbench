"""
Type definitions for the Workbench ConversationContext.

This module provides type annotations for Workbench API classes to ensure
proper type checking and attribute access.
"""

from typing import Any, Protocol

from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    ConversationMessageList,
    ConversationParticipantList,
    NewConversationMessage,
    UpdateParticipant,
)
from semantic_workbench_assistant.assistant_app import ConversationContext


class ConversationAPIClient(Protocol):
    """Protocol defining the shape of a ConversationAPIClient."""

    async def send_message(self, message: NewConversationMessage) -> ConversationMessage: ...

    async def send_messages(self, *messages: NewConversationMessage) -> ConversationMessageList: ...

    async def get_participants(self, include_inactive: bool = False) -> ConversationParticipantList: ...

    async def get_messages(
        self,
        before=None,
        after=None,
        message_types=None,
        participant_ids=None,
        participant_role=None,
        limit=None,
    ) -> ConversationMessageList: ...

    async def update_participant_me(self, participant: UpdateParticipant) -> Any: ...


# Helper functions for working with ConversationContext
def get_conversation_id(context: ConversationContext) -> str:
    """
    Get the conversation ID from a context.
    """
    return str(context.id)
