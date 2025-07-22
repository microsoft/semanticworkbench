"""
Project lifecycle management for Knowledge Transfer Assistant.

Handles project state updates, completion, and lifecycle operations.
"""

from .base import (
    ManagerBase,
    datetime,
    Optional,
    List,
    Tuple,
    ConversationContext,
    ConversationRole,
    KnowledgePackage,
    LogEntryType,
    ShareStorage,
    ProjectNotifier,
    require_current_user,
    logger,
)


class ProjectLifecycleManager(ManagerBase):
    """Manages project lifecycle and state operations."""

    @staticmethod
    async def update_share_state(
        context: ConversationContext,
        status_message: Optional[str] = None,
    ) -> Tuple[bool, Optional[KnowledgePackage]]:
        """
        Updates the knowledge share status message.

        Args:
            context: Current conversation context
            status_message: Optional status message

        Returns:
            Tuple of (success, project_info)
        """
        try:
            from .share_management import ShareManagement
            
            # Get project ID
            share_id = await ShareManagement.get_share_id(context)
            if not share_id:
                logger.error("Cannot update project state: no project associated with this conversation")
                return False, None

            # Get user information
            current_user_id = await require_current_user(context, "update project state")
            if not current_user_id:
                return False, None

            # Get existing project info
            project_info = ShareStorage.read_share_info(share_id)
            if not project_info:
                logger.error(f"Cannot update project state: no project info found for {share_id}")
                return False, None

            # Apply updates
            if status_message:
                project_info.transfer_notes = status_message

            # Update metadata
            project_info.updated_at = datetime.utcnow()

            # Save the project info
            ShareStorage.write_share_info(share_id, project_info)

            # Log the update
            event_type = LogEntryType.STATUS_CHANGED
            message = "Updated status"
            if status_message:
                message += f": {status_message}"

            await ShareStorage.log_share_event(
                context=context,
                share_id=share_id,
                entry_type=event_type.value,
                message=message,
                metadata={
                    "status_message": status_message,
                },
            )

            # Notify linked conversations
            await ProjectNotifier.notify_project_update(
                context=context,
                share_id=share_id,
                update_type="project_state",
                message="KnowledgePackage status updated",
            )

            return True, project_info

        except Exception as e:
            logger.exception(f"Error updating project state: {e}")
            return False, None

    @staticmethod
    async def update_share_info(
        context: ConversationContext,
        progress: Optional[int] = None,
        status_message: Optional[str] = None,
        next_actions: Optional[List[str]] = None,
    ) -> Optional[KnowledgePackage]:
        """
        Updates the project info with progress, status message, and next actions.

        Args:
            context: Current conversation context
            progress: Optional progress percentage (0-100)
            status_message: Optional status message
            next_actions: Optional list of next actions

        Returns:
            Tuple of (success, project_info)
        """
        from .share_management import ShareManagement
        
        # Get project ID
        share_id = await ShareManagement.get_share_id(context)
        if not share_id:
            logger.error("Cannot update project info: no project associated with this conversation")
            return None

        # Get user information
        current_user_id = await require_current_user(context, "update project info")
        if not current_user_id:
            return None

        # Get existing project info
        project_info = ShareStorage.read_share_info(share_id)
        if not project_info:
            logger.error(f"Cannot update project info: no project info found for {share_id}")
            return None

        # Apply updates
        if status_message:
            project_info.transfer_notes = status_message

        if progress is not None:
            project_info.completion_percentage = progress

        if next_actions:
            project_info.next_learning_actions = next_actions

        # Update metadata
        project_info.updated_at = datetime.utcnow()
        project_info.updated_by = current_user_id

        # Increment version if it exists
        if hasattr(project_info, "version"):
            project_info.version += 1

        # Save the project info
        ShareStorage.write_share_info(share_id, project_info)

        # Log the update
        event_type = LogEntryType.STATUS_CHANGED
        message = "Updated status"
        if progress is not None:
            message += f" ({progress}% complete)"
        if status_message:
            message += f": {status_message}"

        await ShareStorage.log_share_event(
            context=context,
            share_id=share_id,
            entry_type=event_type.value,
            message=message,
            metadata={
                "status_message": status_message,
                "progress": progress,
            },
        )

        # Notify linked conversations
        await ProjectNotifier.notify_project_update(
            context=context,
            share_id=share_id,
            update_type="project_info",
            message="KnowledgePackage status updated",
        )

        return project_info

    @staticmethod
    async def complete_project(
        context: ConversationContext,
        summary: Optional[str] = None,
    ) -> Tuple[bool, Optional[KnowledgePackage]]:
        """
        Completes a project and updates the project state.

        Args:
            context: Current conversation context
            summary: Optional summary of project results

        Returns:
            Tuple of (success, project_info)
        """
        try:
            from .share_management import ShareManagement
            
            # Get project ID
            share_id = await ShareManagement.get_share_id(context)
            if not share_id:
                logger.error("Cannot complete project: no project associated with this conversation")
                return False, None

            # Get role - only Coordinator can complete a project
            role = await ShareManagement.get_share_role(context)
            if role != ConversationRole.COORDINATOR:
                logger.error("Only Coordinator can complete a project")
                return False, None

            # Update project state to completed
            status_message = summary if summary else "KnowledgePackage completed successfully"
            success, project_info = await ProjectLifecycleManager.update_share_state(
                context=context,
                status_message=status_message,
            )

            if not success or not project_info:
                return False, None

            # Add completion entry to the log
            await ShareStorage.log_share_event(
                context=context,
                share_id=share_id,
                entry_type=LogEntryType.SHARE_COMPLETED.value,
                message=f"KnowledgePackage completed: {status_message}",
            )

            # Notify linked conversations with emphasis
            await ProjectNotifier.notify_project_update(
                context=context,
                share_id=share_id,
                update_type="project_completed",
                message=f"🎉 PROJECT COMPLETED: {status_message}",
            )

            return True, project_info

        except Exception as e:
            logger.exception(f"Error completing project: {e}")
            return False, None