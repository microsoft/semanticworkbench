from typing import List, Optional

from semantic_workbench_api_model.workbench_model import AssistantStateEvent, MessageType, NewConversationMessage
from semantic_workbench_assistant.assistant_app import ConversationContext

from .data import InspectorTab
from .logging import logger
from .conversation_clients import ConversationClientManager
from .storage import ShareStorage


class Notifications:

    @staticmethod
    async def notify(context: ConversationContext, message: str) -> None:
        """Send text message notification to current conversation only."""
        await context.send_messages(
            NewConversationMessage(
                content=message,
                message_type=MessageType.notice,
            )
        )

    @staticmethod
    async def notify_self_and_other(
        context: ConversationContext,
        share_id: str,
        message: str,
        other_conversation_id: Optional[str] = None
    ) -> None:
        """
        Send text message notification to current conversation and one other.

        If called from team conversation: notifies team + coordinator
        If called from coordinator: notifies coordinator + specified other_conversation_id
        """
        # Always notify current conversation
        await Notifications.notify(context, message)

        knowledge_package = ShareStorage.read_share(share_id)
        if not knowledge_package:
            return

        current_id = str(context.id)

        # Determine the other conversation to notify
        if other_conversation_id:
            target_id = other_conversation_id
        elif knowledge_package.coordinator_conversation_id and knowledge_package.coordinator_conversation_id != current_id:
            target_id = knowledge_package.coordinator_conversation_id
        else:
            return

        try:
            client = ConversationClientManager.get_conversation_client(context, target_id)
            await client.send_messages(
                NewConversationMessage(
                    content=message,
                    message_type=MessageType.notice,
                )
            )
        except Exception as e:
            logger.error(f"Failed to notify conversation {target_id}: {e}")

    @staticmethod
    async def notify_all(context: ConversationContext, share_id: str, message: str) -> None:
        """Send text message notification to all knowledge transfer conversations."""

        knowledge_package = ShareStorage.read_share(share_id)
        if not knowledge_package:
            return

        # Always notify current conversation
        await Notifications.notify(context, message)

        current_id = str(context.id)

        # Notify coordinator conversation
        if knowledge_package.coordinator_conversation_id and knowledge_package.coordinator_conversation_id != current_id:
            try:
                client = ConversationClientManager.get_conversation_client(
                    context, knowledge_package.coordinator_conversation_id
                )
                await client.send_messages(
                    NewConversationMessage(
                        content=message,
                        message_type=MessageType.notice,
                    )
                )
            except Exception as e:
                logger.error(f"Failed to notify coordinator conversation: {e}")

        # Notify all team conversations
        for conv_id in knowledge_package.team_conversations.keys():
            if conv_id != current_id and conv_id != knowledge_package.coordinator_conversation_id:
                try:
                    client = ConversationClientManager.get_conversation_client(context, conv_id)
                    await client.send_messages(
                        NewConversationMessage(
                            content=message,
                            message_type=MessageType.notice,
                        )
                    )
                except Exception as e:
                    logger.error(f"Failed to notify conversation {conv_id}: {e}")

    # State Update Notifications (UI refreshes)

    @staticmethod
    async def notify_state_update(context: ConversationContext, tabs: List[InspectorTab]) -> None:
        """Send state update notifications to refresh UI in current conversation only."""
        for tab in tabs:
            state_event = AssistantStateEvent(
                state_id=tab.value,
                event="updated",
                state=None,
            )
            await context.send_conversation_state_event(state_event)

    @staticmethod
    async def notify_all_state_update(context: ConversationContext, share_id: str, tabs: List[InspectorTab]) -> None:
        """Send state update notifications to refresh UI across all project conversations."""

        # Refresh current conversation first
        await Notifications.notify_state_update(context, tabs)

        # Refresh other conversations
        knowledge_package = ShareStorage.read_share(share_id)
        if not knowledge_package:
            return

        current_id = str(context.id)
        assistant_id = context.assistant.id

        # Refresh coordinator conversation
        if knowledge_package.coordinator_conversation_id and knowledge_package.coordinator_conversation_id != current_id:
            try:
                client = ConversationClientManager.get_conversation_client(
                    context, knowledge_package.coordinator_conversation_id
                )

                for tab in tabs:
                    state_event = AssistantStateEvent(
                        state_id=tab.value,
                        event="updated",
                        state=None,
                    )
                    await client.send_conversation_state_event(
                        state_event=state_event,
                        assistant_id=assistant_id,
                    )
            except Exception as e:
                logger.error(f"Failed to refresh coordinator conversation UI: {e}")

        # Refresh all team conversations
        for conv_id in knowledge_package.team_conversations.keys():
            if conv_id != current_id and conv_id != knowledge_package.coordinator_conversation_id:
                try:
                    client = ConversationClientManager.get_conversation_client(context, conv_id)

                    for tab in tabs:
                        state_event = AssistantStateEvent(
                            state_id=tab.value,
                            event="updated",
                            state=None,
                        )
                        await client.send_conversation_state_event(
                            state_event=state_event,
                            assistant_id=assistant_id,
                        )
                except Exception as e:
                    logger.error(f"Failed to refresh conversation {conv_id} UI: {e}")
