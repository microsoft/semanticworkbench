"""
Type definitions for the Workbench ConversationContext.

This module provides type annotations for Workbench API classes to ensure
proper type checking and attribute access.
"""

from typing import Any, Protocol, cast

from semantic_workbench_assistant.assistant_app import ConversationContext
from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    ConversationMessageList,
    ConversationParticipantList,
    NewConversationMessage,
    UpdateParticipant,
)


class Conversation(Protocol):
    """Protocol defining the shape of a Conversation object."""

    id: str
    title: str


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


# Extend ConversationContext with necessary attributes
class ConversationContextExt(Protocol):
    """Protocol defining the extended shape of ConversationContext."""

    conversation: Conversation

    async def send_messages(
        self, messages: NewConversationMessage | list[NewConversationMessage]
    ) -> ConversationMessageList: ...

    async def get_participants(self, include_inactive=False) -> ConversationParticipantList: ...

    async def get_messages(
        self,
        before=None,
        after=None,
        message_types=None,
        participant_ids=None,
        participant_role=None,
        limit=None,
    ) -> ConversationMessageList: ...


# Helper functions for working with ConversationContext
def get_conversation_id(context: ConversationContext) -> str:
    """
    Safely get the conversation ID from a context.
    This function casts the context to the extended version to access the 'conversation' attribute.

    Args:
        context: The conversation context

    Returns:
        The conversation ID as a string
    """
    # Cast to extended context type to satisfy type checker
    ctx_ext = cast(ConversationContextExt, context)
    return str(ctx_ext.conversation.id)
