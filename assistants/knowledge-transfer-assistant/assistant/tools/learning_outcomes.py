"""
Learning outcomes management tools for Knowledge Transfer Assistant.

Tools for managing individual learning outcomes within objectives.
"""


from semantic_workbench_api_model.workbench_model import (
    MessageType,
    NewConversationMessage,
)

from ..data import LogEntryType
from ..manager import KnowledgeTransferManager
from ..notifications import ProjectNotifier
from ..storage import ShareStorage
from ..storage_models import ConversationRole
from ..utils import require_current_user
from .base import ToolsBase


class LearningOutcomeTools(ToolsBase):
    """Tools for managing learning outcomes."""

    async def add_learning_outcome(self, objective_id: str, outcome_description: str) -> str:
        """
        Add a new learning outcome to an existing learning objective.

        WHEN TO USE:
        - When you need to add additional measurable outcomes to an existing objective
        - When refining objectives by breaking them down into more specific outcomes
        - When expanding the scope of an objective with new learning goals
        - When iteratively developing learning objectives based on feedback

        Args:
            objective_id: The unique ID of the learning objective to add the outcome to
            outcome_description: Clear, specific description of what needs to be understood or accomplished

        Returns:
            A message indicating success or failure
        """
        if self.role is not ConversationRole.COORDINATOR:
            return "Only Coordinator can add learning outcomes."

        # Get share ID
        share_id = await KnowledgeTransferManager.get_share_id(self.context)
        if not share_id:
            return "No knowledge package associated with this conversation. Please create a knowledge brief first."

        # Get existing knowledge package
        knowledge_package = ShareStorage.read_share(share_id)
        if not knowledge_package or not knowledge_package.learning_objectives:
            return "No learning objectives found. Please add objectives before adding outcomes."

        # Find the objective by ID
        objective = None
        for obj in knowledge_package.learning_objectives:
            if obj.id == objective_id:
                objective = obj
                break

        if objective is None:
            available_ids = [obj.id for obj in knowledge_package.learning_objectives]
            return f"Learning objective with ID '{objective_id}' not found. Available objective IDs: {', '.join(available_ids[:3]) + ('...' if len(available_ids) > 3 else '')}"

        # Import here to avoid circular imports
        from ..data import LearningOutcome

        # Create the new outcome
        new_outcome = LearningOutcome(description=outcome_description.strip())

        # Add the outcome to the objective
        objective.learning_outcomes.append(new_outcome)

        # Get user information for logging
        current_user_id = await require_current_user(self.context, "add learning outcome")
        if not current_user_id:
            return "Could not identify current user."

        # Save the updated knowledge package
        ShareStorage.write_share(share_id, knowledge_package)

        # Log the outcome addition
        await ShareStorage.log_share_event(
            context=self.context,
            share_id=share_id,
            entry_type=LogEntryType.LEARNING_OBJECTIVE_UPDATED.value,
            message=f"Added learning outcome to objective '{objective.name}': {outcome_description}",
            metadata={
                "objective_id": objective_id,
                "objective_name": objective.name,
                "outcome_added": outcome_description,
                "outcome_id": new_outcome.id,
            },
        )

        # Notify linked conversations
        await ProjectNotifier.notify_project_update(
            context=self.context,
            share_id=share_id,
            update_type="learning_objective",
            message=f"New learning outcome added to objective '{objective.name}'",
        )

        # Update all share UI inspectors
        await ShareStorage.refresh_all_share_uis(self.context, share_id)

        # Send notification to current conversation
        await self.context.send_messages(
            NewConversationMessage(
                content=f"Learning outcome added successfully to objective '{objective.name}': {outcome_description}",
                message_type=MessageType.notice,
            )
        )

        return f"Learning outcome added successfully to objective '{objective.name}': {outcome_description}"

    async def update_learning_outcome(self, outcome_id: str, new_description: str) -> str:
        """
        Update the description of an existing learning outcome.

        WHEN TO USE:
        - When clarifying or improving the wording of an existing outcome
        - When making outcomes more specific or measurable
        - When correcting errors in outcome descriptions
        - When refining outcomes based on feedback or better understanding

        Args:
            outcome_id: The unique ID of the learning outcome to update
            new_description: New description for the learning outcome

        Returns:
            A message indicating success or failure
        """
        if self.role is not ConversationRole.COORDINATOR:
            return "Only Coordinator can update learning outcomes."

        # Get share ID
        share_id = await KnowledgeTransferManager.get_share_id(self.context)
        if not share_id:
            return "No knowledge package associated with this conversation. Please create a knowledge brief first."

        # Get existing knowledge package
        knowledge_package = ShareStorage.read_share(share_id)
        if not knowledge_package or not knowledge_package.learning_objectives:
            return "No learning objectives found. Please add objectives before updating outcomes."

        # Find the outcome by ID across all objectives
        objective = None
        outcome = None
        for obj in knowledge_package.learning_objectives:
            for out in obj.learning_outcomes:
                if out.id == outcome_id:
                    objective = obj
                    outcome = out
                    break
            if outcome:
                break

        if outcome is None or objective is None:
            # Collect available outcome IDs for error message
            available_outcome_ids = []
            for obj in knowledge_package.learning_objectives:
                for out in obj.learning_outcomes:
                    available_outcome_ids.append(out.id)
            return f"Learning outcome with ID '{outcome_id}' not found. Available outcome IDs: {', '.join(available_outcome_ids[:3]) + ('...' if len(available_outcome_ids) > 3 else '')}"

        old_description = outcome.description

        # Update the outcome description
        outcome.description = new_description.strip()

        # Get user information for logging
        current_user_id = await require_current_user(self.context, "update learning outcome")
        if not current_user_id:
            return "Could not identify current user."

        # Save the updated knowledge package
        ShareStorage.write_share(share_id, knowledge_package)

        # Log the outcome update
        await ShareStorage.log_share_event(
            context=self.context,
            share_id=share_id,
            entry_type=LogEntryType.LEARNING_OBJECTIVE_UPDATED.value,
            message=f"Updated learning outcome in objective '{objective.name}': '{old_description}' → '{new_description}'",
            metadata={
                "objective_id": objective.id,
                "objective_name": objective.name,
                "outcome_id": outcome_id,
                "old_description": old_description,
                "new_description": new_description,
            },
        )

        # Notify linked conversations
        await ProjectNotifier.notify_project_update(
            context=self.context,
            share_id=share_id,
            update_type="learning_objective",
            message=f"Learning outcome updated in objective '{objective.name}'",
        )

        # Update all share UI inspectors
        await ShareStorage.refresh_all_share_uis(self.context, share_id)

        # Send notification to current conversation
        await self.context.send_messages(
            NewConversationMessage(
                content=f"Learning outcome updated successfully in objective '{objective.name}': {new_description}",
                message_type=MessageType.notice,
            )
        )

        return f"Learning outcome updated successfully in objective '{objective.name}': {new_description}"

    async def delete_learning_outcome(self, outcome_id: str) -> str:
        """
        Delete a learning outcome from a learning objective.

        WHEN TO USE:
        - When an outcome is no longer relevant or necessary
        - When consolidating redundant outcomes
        - When removing outcomes that were added by mistake
        - When simplifying objectives by removing overly specific outcomes

        NOTE: This action is irreversible. Use get_project_info() first to see the current outcomes and their IDs.

        Args:
            outcome_id: The unique ID of the learning outcome to delete

        Returns:
            A message indicating success or failure
        """
        if self.role is not ConversationRole.COORDINATOR:
            return "Only Coordinator can delete learning outcomes."

        # Get share ID
        share_id = await KnowledgeTransferManager.get_share_id(self.context)
        if not share_id:
            return "No knowledge package associated with this conversation. Please create a knowledge brief first."

        # Get existing knowledge package
        knowledge_package = ShareStorage.read_share(share_id)
        if not knowledge_package or not knowledge_package.learning_objectives:
            return "No learning objectives found. Please add objectives before deleting outcomes."

        # Find the outcome by ID across all objectives
        objective = None
        outcome_to_delete = None
        outcome_index = -1
        for obj in knowledge_package.learning_objectives:
            for idx, out in enumerate(obj.learning_outcomes):
                if out.id == outcome_id:
                    objective = obj
                    outcome_to_delete = out
                    outcome_index = idx
                    break
            if outcome_to_delete:
                break

        if outcome_to_delete is None or objective is None:
            # Collect available outcome IDs for error message
            available_outcome_ids = []
            for obj in knowledge_package.learning_objectives:
                for out in obj.learning_outcomes:
                    available_outcome_ids.append(out.id)
            return f"Learning outcome with ID '{outcome_id}' not found. Available outcome IDs: {', '.join(available_outcome_ids[:3]) + ('...' if len(available_outcome_ids) > 3 else '')}"

        deleted_description = outcome_to_delete.description

        # Remove the outcome from the objective
        objective.learning_outcomes.pop(outcome_index)

        # Get user information for logging
        current_user_id = await require_current_user(self.context, "delete learning outcome")
        if not current_user_id:
            return "Could not identify current user."

        # Clean up any achievement records for this outcome across all team conversations
        for team_info in knowledge_package.team_conversations.values():
            team_info.outcome_achievements = [
                achievement for achievement in team_info.outcome_achievements
                if achievement.outcome_id != outcome_id
            ]

        # Save the updated knowledge package
        ShareStorage.write_share(share_id, knowledge_package)

        # Log the outcome deletion
        await ShareStorage.log_share_event(
            context=self.context,
            share_id=share_id,
            entry_type=LogEntryType.LEARNING_OBJECTIVE_UPDATED.value,
            message=f"Deleted learning outcome from objective '{objective.name}': {deleted_description}",
            metadata={
                "objective_id": objective.id,
                "objective_name": objective.name,
                "outcome_index": outcome_index,
                "outcome_id": outcome_id,
                "deleted_description": deleted_description,
            },
        )

        # Notify linked conversations
        await ProjectNotifier.notify_project_update(
            context=self.context,
            share_id=share_id,
            update_type="learning_objective",
            message=f"Learning outcome removed from objective '{objective.name}'",
        )

        # Update all share UI inspectors
        await ShareStorage.refresh_all_share_uis(self.context, share_id)

        # Send notification to current conversation
        await self.context.send_messages(
            NewConversationMessage(
                content=f"Learning outcome deleted successfully from objective '{objective.name}': {deleted_description}",
                message_type=MessageType.notice,
            )
        )

        return f"Learning outcome deleted successfully from objective '{objective.name}': {deleted_description}"