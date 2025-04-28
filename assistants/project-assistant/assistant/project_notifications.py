"""
Project notification and UI refresh functionality.

This module handles notifications between conversations and UI refresh events
for the project assistant, ensuring all participants stay in sync.
"""

from typing import Any, Dict, Optional

from semantic_workbench_api_model.workbench_model import AssistantStateEvent, MessageType, NewConversationMessage
from semantic_workbench_assistant.assistant_app import ConversationContext

from .logging import logger
from .project_storage import ProjectStorage


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
        from .conversation_project_link import ConversationProjectManager

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
    from .conversation_project_link import ConversationProjectManager

    try:
        # First update the current conversation's UI
        await refresh_current_ui(context)

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