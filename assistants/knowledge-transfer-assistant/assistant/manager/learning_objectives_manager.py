"""
Learning objectives and outcomes management for Knowledge Transfer Assistant.

Handles learning objectives, outcomes creation, updates, and deletion.
"""

from .base import (
    ManagerBase,
    datetime,
    Optional,
    List,
    Tuple,
    ConversationContext,
    LearningObjective,
    LearningOutcome,
    KnowledgePackage,
    ShareStorage,
    LogEntryType,
    ProjectNotifier,
    require_current_user,
    logger,
)


class LearningObjectivesManager(ManagerBase):
    """Manages learning objectives and outcomes operations."""

    @staticmethod
    async def add_learning_objective(
        context: ConversationContext,
        objective_name: str,
        description: str,
        outcomes: Optional[List[str]] = None,
        priority: int = 1,
    ) -> Optional[LearningObjective]:
        """
        Adds a learning objective to the project.

        Args:
            context: Current conversation context
            objective_name: Name of the learning objective
            description: Description of the learning objective
            outcomes: List of learning outcome strings (optional)
            priority: Priority of the learning objective (default: 1)

        Returns:
            The created LearningObjective if successful, None otherwise
        """
        from .share_management import ShareManagement
        
        # Get project ID
        share_id = await ShareManagement.get_share_id(context)
        if not share_id:
            logger.error("Cannot add learning objective: no project associated with this conversation")
            return None

        # Get user information
        current_user_id = await require_current_user(context, "add learning objective")
        if not current_user_id:
            return None

        # Create success criteria objects if provided
        criterion_objects = []
        if outcomes:
            for criterion in outcomes:
                criterion_objects.append(LearningOutcome(description=criterion))

        # Create the new learning objective
        new_learning_objective = LearningObjective(
            name=objective_name,
            description=description,
            priority=priority,
            learning_outcomes=criterion_objects,
        )

        # Get the existing project
        project = ShareStorage.read_share(share_id)
        if not project:
            # Create a new project if it doesn't exist
            project = KnowledgePackage(
                share_id=share_id,
                brief=None,
                learning_objectives=[new_learning_objective],
                digest=None,
                requests=[],
                log=None,
            )
        else:
            # Add the learning objective to the existing project
            project.learning_objectives.append(new_learning_objective)

        # Save the updated project
        ShareStorage.write_share(share_id, project)

        # Log the learning objective addition
        await ShareStorage.log_share_event(
            context=context,
            share_id=share_id,
            entry_type=LogEntryType.LEARNING_OBJECTIVE_ADDED.value,
            message=f"Added learning objective: {objective_name}",
        )

        # Notify linked conversations
        await ProjectNotifier.notify_project_update(
            context=context,
            share_id=share_id,
            update_type="learning objective",
            message=f"learning objective added: {objective_name}",
        )

        return new_learning_objective

    @staticmethod
    async def delete_learning_objective(
        context: ConversationContext,
        objective_index: int,
    ) -> Tuple[bool, Optional[str]]:
        """
        Deletes a learning objective from the project.

        Args:
            context: Current conversation context
            objective_index: The index of the learning objective to delete (0-based)

        Returns:
            Tuple of (success, objective_name_or_error_message)
        """
        from .share_management import ShareManagement
        
        # Get project ID
        share_id = await ShareManagement.get_share_id(context)
        if not share_id:
            logger.error("Cannot delete learning objective: no project associated with this conversation")
            return False, "No project associated with this conversation."

        # Get user information
        current_user_id = await require_current_user(context, "delete learning objective")
        if not current_user_id:
            return False, "Could not identify current user."

        # Get the existing project
        project = ShareStorage.read_share(share_id)
        if not project or not project.learning_objectives:
            return False, "No project learning objectives found."

        # Validate index
        if objective_index < 0 or objective_index >= len(project.learning_objectives):
            return (
                False,
                f"Invalid learning objective index {objective_index}. Valid indexes are 0 to {len(project.learning_objectives) - 1}. There are {len(project.learning_objectives)} learning objectives.",
            )

        # Get the learning objective to delete
        learning_objective = project.learning_objectives[objective_index]
        learning_objective_name = learning_objective.name

        # Remove the learning objective from the list
        project.learning_objectives.pop(objective_index)

        # Save the updated project
        ShareStorage.write_share(share_id, project)

        # Log the learning objective deletion
        await ShareStorage.log_share_event(
            context=context,
            share_id=share_id,
            entry_type=LogEntryType.LEARNING_OBJECTIVE_DELETED.value,
            message=f"Deleted learning objective: {learning_objective_name}",
        )

        # Notify linked conversations
        await ProjectNotifier.notify_project_update(
            context=context,
            share_id=share_id,
            update_type="learning objective",
            message=f"learning objective deleted: {learning_objective_name}",
        )

        # Update project info with new criteria counts
        project_info = ShareStorage.read_share_info(share_id)
        if project_info:
            # Count all completed criteria
            completed_criteria = 0
            total_criteria = 0

            # Get the updated project to access learning objectives
            updated_project = ShareStorage.read_share(share_id)
            if updated_project:
                # Use the new overall completion calculation
                completed_criteria, total_criteria = updated_project.get_overall_completion()

                # Calculate progress percentage
                if total_criteria > 0:
                    project_info.completion_percentage = int((completed_criteria / total_criteria) * 100)
                else:
                    project_info.completion_percentage = 0

            # Update metadata
            project_info.updated_at = datetime.utcnow()
            project_info.updated_by = current_user_id
            project_info.version += 1

            # Save the updated project info
            ShareStorage.write_share_info(share_id, project_info)

        # Update all project UI inspectors
        await ShareStorage.refresh_all_share_uis(context, share_id)

        return True, learning_objective_name

    @staticmethod
    async def get_learning_outcomes(context: ConversationContext) -> List[LearningOutcome]:
        """
        Gets the learning outcomes for the current knowledge share.

        Args:
            context: Current conversation context
            completed_only: If True, only return completed criteria

        Returns:
            List of LearningOutcome objects
        """
        from .share_management import ShareManagement
        
        share_id = await ShareManagement.get_share_id(context)
        if not share_id:
            return []

        # Get the project which contains learning objectives and success criteria
        project = ShareStorage.read_share(share_id)
        if not project:
            return []

        objectives = project.learning_objectives
        outcomes = []
        for objective in objectives:
            # Add success criteria from each learning objective
            outcomes.extend(objective.learning_outcomes)

        return outcomes