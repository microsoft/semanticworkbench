"""
Learning objectives management tools for Knowledge Transfer Assistant.

Tools for creating, updating, and managing learning objectives and outcomes.
"""

from typing import List

from semantic_workbench_api_model.workbench_model import (
    MessageType,
    NewConversationMessage,
)

from ..data import LogEntryType
from ..logging import logger
from ..manager import KnowledgeTransferManager
from ..notifications import ProjectNotifier
from ..storage import ShareStorage
from ..storage_models import ConversationRole
from ..utils import require_current_user
from .base import ToolsBase


class LearningObjectiveTools(ToolsBase):
    """Tools for managing learning objectives and outcomes."""

    async def add_learning_objective(self, objective_name: str, description: str, learning_outcomes: List[str]) -> str:
        """
        Add a learning objective with measurable learning outcomes.

        - Learning objectives should define what knowledge areas learners need to understand.
        - Each objective must have clear, measurable learning outcomes that learners can mark as achieved.

        WHEN TO USE:
        - When defining what knowledge areas team members need to understand
        - When breaking down knowledge requirements into specific, learnable objectives
        - After creating a knowledge brief, before marking the transfer ready for learning
        - When users ask to add or define learning objectives or knowledge areas

        Args:
            objective_name: A concise, clear name for the learning objective (e.g., "Understanding User Authentication")
            description: A detailed description explaining what knowledge needs to be understood
            learning_outcomes: List of specific, measurable outcomes that indicate when the objective is achieved
                             (e.g., ["Can explain authentication flow", "Can implement password security"])

        Returns:
            A message indicating success or failure
        """

        if self.role is not ConversationRole.COORDINATOR:
            return "Only Coordinator can add learning objectives."

        share_id = await KnowledgeTransferManager.get_share_id(self.context)
        if not share_id:
            return "No knowledge package associated with this conversation. Please create a knowledge brief first."

        brief = await KnowledgeTransferManager.get_knowledge_brief(self.context)
        if not brief:
            return "No knowledge brief found. Please create one first with update_brief."
        try:
            objective = await KnowledgeTransferManager.add_learning_objective(
                context=self.context,
                objective_name=objective_name,
                description=description,
                outcomes=learning_outcomes,
            )

            if objective:
                return f"Learning objective '{objective_name}' added to knowledge brief successfully."
            else:
                return "Failed to add learning objective. Please try again."
        except Exception as e:
            logger.exception(f"Error adding learning objective: {e}")
            return f"Error adding learning objective: {str(e)}"

    async def update_learning_objective(
        self,
        objective_id: str,
        objective_name: str,
        description: str,
    ) -> str:
        """
        Update an existing learning objective's name or description.

        Args:
            objective_id: The unique ID of the learning objective to update
            objective_name: New name for the objective (empty string to keep current name)
            description: New description (empty string to keep current description)

        Returns:
            A message indicating success or failure
        """
        if self.role is not ConversationRole.COORDINATOR:
            return "Only Coordinator can update learning objectives."

        # Get share ID
        share_id = await KnowledgeTransferManager.get_share_id(self.context)
        if not share_id:
            return "No knowledge package associated with this conversation. Please create a knowledge brief first."

        # Get existing knowledge package
        knowledge_package = ShareStorage.read_share(share_id)
        if not knowledge_package or not knowledge_package.learning_objectives:
            return "No learning objectives found. Please add objectives before updating them."

        # Find the objective by ID
        objective = None
        for obj in knowledge_package.learning_objectives:
            if obj.id == objective_id:
                objective = obj
                break

        if objective is None:
            available_ids = [obj.id for obj in knowledge_package.learning_objectives]
            return f"Learning objective with ID '{objective_id}' not found. Available objective IDs: {', '.join(available_ids[:3]) + ('...' if len(available_ids) > 3 else '')}"
        original_name = objective.name

        # Update fields if provided (empty string/list means no change)
        if objective_name.strip():
            objective.name = objective_name.strip()

        if description.strip():
            objective.description = description.strip()

        # Get user information for logging
        current_user_id = await require_current_user(self.context, "update learning objective")
        if not current_user_id:
            return "Could not identify current user."

        # Save the updated knowledge package
        ShareStorage.write_share(share_id, knowledge_package)

        # Log the objective update
        changes_made = []
        if objective_name.strip():
            changes_made.append(f"name: '{original_name}' → '{objective_name.strip()}'")
        if description.strip():
            changes_made.append("description updated")

        changes_text = ", ".join(changes_made) if changes_made else "no changes specified"

        await ShareStorage.log_share_event(
            context=self.context,
            share_id=share_id,
            entry_type=LogEntryType.LEARNING_OBJECTIVE_UPDATED.value,
            message=f"Updated learning objective '{objective.name}': {changes_text}",
            metadata={
                "objective_id": objective_id,
                "objective_name": objective.name,
                "changes": changes_text,
            },
        )

        # Notify linked conversations
        await ProjectNotifier.notify_project_update(
            context=self.context,
            share_id=share_id,
            update_type="learning_objective",
            message=f"Learning objective '{objective.name}' has been updated",
        )

        # Update all share UI inspectors
        await ShareStorage.refresh_all_share_uis(self.context, share_id)

        # Send notification to current conversation
        await self.context.send_messages(
            NewConversationMessage(
                content=f"Learning objective '{objective.name}' has been successfully updated: {changes_text}.",
                message_type=MessageType.notice,
            )
        )

        return f"Learning objective '{objective.name}' has been successfully updated: {changes_text}."

    async def delete_learning_objective(self, objective_id: str) -> str:
        """
        Delete a learning objective from the knowledge package by ID.

        WHEN TO USE:
        - When a user explicitly requests to remove or delete a specific learning objective
        - When objectives need to be reorganized and redundant/obsolete objectives removed
        - When an objective was added by mistake or is no longer relevant to the knowledge transfer
        - Only before marking the knowledge package as ready for transfer

        NOTE: This action is irreversible and will remove all learning outcomes associated with the objective.

        Args:
            objective_id: The unique ID of the learning objective to delete.

        Returns:
            A message indicating success or failure
        """

        if self.role is not ConversationRole.COORDINATOR:
            return "Only Coordinator can delete learning objectives."

        # Get share ID
        share_id = await KnowledgeTransferManager.get_share_id(self.context)
        if not share_id:
            return "No knowledge package associated with this conversation. Please create a knowledge brief first."

        # Get existing knowledge package
        knowledge_package = ShareStorage.read_share(share_id)
        if not knowledge_package or not knowledge_package.learning_objectives:
            return "No learning objectives found. Please add objectives before deleting them."

        # Find the objective by ID
        objective = None
        objective_index = -1
        for idx, obj in enumerate(knowledge_package.learning_objectives):
            if obj.id == objective_id:
                objective = obj
                objective_index = idx
                break

        if objective is None:
            available_ids = [obj.id for obj in knowledge_package.learning_objectives]
            return f"Learning objective with ID '{objective_id}' not found. Available objective IDs: {', '.join(available_ids[:3]) + ('...' if len(available_ids) > 3 else '')}"

        objective_name = objective.name

        # Get user information for logging
        current_user_id = await require_current_user(self.context, "delete learning objective")
        if not current_user_id:
            return "Could not identify current user."

        # Clean up any achievement records for all outcomes in this objective across all team conversations
        for outcome in objective.learning_outcomes:
            for team_info in knowledge_package.team_conversations.values():
                team_info.outcome_achievements = [
                    achievement for achievement in team_info.outcome_achievements
                    if achievement.outcome_id != outcome.id
                ]

        # Remove the objective from the knowledge package
        knowledge_package.learning_objectives.pop(objective_index)

        # Save the updated knowledge package
        ShareStorage.write_share(share_id, knowledge_package)

        # Log the objective deletion
        await ShareStorage.log_share_event(
            context=self.context,
            share_id=share_id,
            entry_type=LogEntryType.LEARNING_OBJECTIVE_UPDATED.value,
            message=f"Deleted learning objective '{objective_name}' and all its outcomes",
            metadata={
                "objective_id": objective_id,
                "objective_name": objective_name,
                "outcomes_count": len(objective.learning_outcomes),
            },
        )

        # Notify linked conversations
        await ProjectNotifier.notify_project_update(
            context=self.context,
            share_id=share_id,
            update_type="learning_objective",
            message=f"Learning objective '{objective_name}' has been deleted",
        )

        # Update all share UI inspectors
        await ShareStorage.refresh_all_share_uis(self.context, share_id)

        # Send notification to current conversation
        await self.context.send_messages(
            NewConversationMessage(
                content=f"Learning objective '{objective_name}' has been successfully deleted from the knowledge package.",
                message_type=MessageType.notice,
            )
        )

        return f"Learning objective '{objective_name}' has been successfully deleted from the knowledge package."