"""
Knowledge brief management operations for Knowledge Transfer Assistant.

Handles knowledge brief creation, updates, and retrieval.
"""

from .base import (
    ManagerBase,
    Optional,
    ConversationContext,
    KnowledgeBrief,
    ShareStorage,
    LogEntryType,
    ProjectNotifier,
    InspectorTab,
    require_current_user,
    logger,
)


class KnowledgeBriefManager(ManagerBase):
    """Manages knowledge brief operations."""

    @staticmethod
    async def get_knowledge_brief(context: ConversationContext) -> Optional[KnowledgeBrief]:
        """
        Gets the brief for the current conversation's knowledge share.

        The brief contains the core information about the knowledge share:
        name, description, learning objectives, and success criteria. This is the central
        document that defines what the knowledge share is trying to accomplish.

        Args:
            context: Current conversation context

        Returns:
            The KnowledgeBrief object if found, None if the conversation is not
            part of a knowledge share or if no brief has been created yet
        """
        from .share_management import ShareManagement
        
        share_id = await ShareManagement.get_share_id(context)
        if not share_id:
            return None

        return ShareStorage.read_knowledge_brief(share_id)

    @staticmethod
    async def update_knowledge_brief(
        context: ConversationContext,
        title: str,
        description: str,
        timeline: Optional[str] = None,
        send_notification: bool = True,
    ) -> Optional[KnowledgeBrief]:
        """
        Creates or updates a knowledge brief for the current knowledge share.

        The brief is the primary document that defines the knowledge share for team members.

        Args:
            context: A reference to the conversation context object
            title: Short, descriptive name for the knowledge share
            description: Comprehensive description of the knowledge share's purpose
            timeline: Optional information about timeline/deadlines
            send_notification: Whether to send a notification about the brief update (default: True)

        Returns:
            The updated KnowledgeBrief object if successful, None otherwise
        """
        from .share_management import ShareManagement
        
        # Get project ID
        share_id = await ShareManagement.get_share_id(context)
        if not share_id:
            logger.error("Cannot update brief: no project associated with this conversation")
            return
        # Get user information
        current_user_id = await require_current_user(context, "update brief")
        if not current_user_id:
            return

        # Create the project brief
        brief = KnowledgeBrief(
            title=title,
            content=description,
            timeline=timeline,
            created_by=current_user_id,
            updated_by=current_user_id,
            conversation_id=str(context.id),
        )

        # Save the brief
        ShareStorage.write_knowledge_brief(share_id, brief)

        # Check if this is a creation or an update
        existing_brief = ShareStorage.read_knowledge_brief(share_id)
        if existing_brief:
            # This is an update
            await ShareStorage.log_share_event(
                context=context,
                share_id=share_id,
                entry_type=LogEntryType.BRIEFING_UPDATED.value,
                message=f"Updated brief: {title}",
            )
        else:
            # This is a creation
            await ShareStorage.log_share_event(
                context=context,
                share_id=share_id,
                entry_type=LogEntryType.BRIEFING_CREATED.value,
                message=f"Created brief: {title}",
            )

        # Only notify if send_notification is True
        if send_notification:
            # Notify linked conversations
            await ProjectNotifier.notify_project_update(
                context=context,
                share_id=share_id,
                update_type="brief",
                message=f"Brief created: {title}",
                tabs=[InspectorTab.BRIEF],
            )

        return brief