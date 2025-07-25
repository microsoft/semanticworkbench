"""
Learning objectives and outcomes management for Knowledge Transfer Assistant.

Handles learning objectives, outcomes creation, updates, and deletion.
"""

from typing import List, Optional, Tuple

from semantic_workbench_assistant.assistant_app import ConversationContext

from ..data import InspectorTab, KnowledgePackage, LearningObjective, LearningOutcome, LogEntryType
from ..logging import logger
from ..notifications import Notifications
from ..storage import ShareStorage
from ..utils import require_current_user
from .share_manager import ShareManager

class LearningObjectivesManager:
    """Manages learning objectives and outcomes operations."""

    @staticmethod
    async def add_learning_objective(
        context: ConversationContext,
        objective_name: str,
        description: str,
        outcomes: Optional[List[str]] = None,
        priority: int = 1,
    ) -> Optional[LearningObjective]:

        share_id = await ShareManager.get_share_id(context)
        if not share_id:
            logger.error("Cannot add learning objective: no share associated with this conversation")
            return None

        current_user_id = await require_current_user(context, "add learning objective")
        if not current_user_id:
            return None

        criterion_objects = []
        if outcomes:
            for criterion in outcomes:
                criterion_objects.append(LearningOutcome(description=criterion))

        new_learning_objective = LearningObjective(
            name=objective_name,
            description=description,
            priority=priority,
            learning_outcomes=criterion_objects,
        )

        share = ShareStorage.read_share(share_id)
        if not share:
            # Create a new share if it doesn't exist
            share = KnowledgePackage(
                share_id=share_id,
                brief=None,
                learning_objectives=[new_learning_objective],
                digest=None,
                requests=[],
                log=None,
            )
        else:
            share.learning_objectives.append(new_learning_objective)

        ShareStorage.write_share(share_id, share)

        await ShareStorage.log_share_event(
            context=context,
            share_id=share_id,
            entry_type=LogEntryType.LEARNING_OBJECTIVE_ADDED.value,
            message=f"Added learning objective: {objective_name}",
        )

        await Notifications.notify_all(context, share_id, f"Learning objective '{objective_name}' was added")
        await Notifications.notify_all_state_update(context, share_id, [InspectorTab.LEARNING, InspectorTab.BRIEF])

        return new_learning_objective

    @staticmethod
    async def update_learning_objective(
        context: ConversationContext,
        objective_id: str,
        objective_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Update an existing learning objective's name or description."""
        share_id = await ShareManager.get_share_id(context)
        if not share_id:
            logger.error("Cannot update learning objective: no share associated with this conversation")
            return False, "No share associated with this conversation."

        current_user_id = await require_current_user(context, "update learning objective")
        if not current_user_id:
            return False, "Could not identify current user."

        share = ShareStorage.read_share(share_id)
        if not share or not share.learning_objectives:
            return False, "No learning objectives found."

        # Find objective by ID
        objective = None
        for obj in share.learning_objectives:
            if obj.id == objective_id:
                objective = obj
                break

        if not objective:
            available_ids = [obj.id for obj in share.learning_objectives]
            return False, f"Learning objective with ID '{objective_id}' not found. Available objective IDs: {', '.join(available_ids[:3]) + ('...' if len(available_ids) > 3 else '')}"

        original_name = objective.name
        changes_made = []

        # Update fields if provided
        if objective_name and objective_name.strip():
            objective.name = objective_name.strip()
            changes_made.append(f"name: '{original_name}' → '{objective_name.strip()}'")

        if description and description.strip():
            objective.description = description.strip()
            changes_made.append("description updated")

        if not changes_made:
            return True, "No changes specified"

        ShareStorage.write_share(share_id, share)

        changes_text = ", ".join(changes_made)
        await ShareStorage.log_share_event(
            context=context,
            share_id=share_id,
            entry_type=LogEntryType.LEARNING_OBJECTIVE_UPDATED.value,
            message=f"Updated learning objective '{objective.name}': {changes_text}",
            metadata={
                "objective_id": objective_id,
                "objective_name": objective.name,
                "changes": changes_text,
            },
        )

        await Notifications.notify_all(context, share_id, f"Learning objective '{objective.name}' has been updated")
        await Notifications.notify_all_state_update(context, share_id, [InspectorTab.LEARNING, InspectorTab.BRIEF])

        return True, f"Learning objective '{objective.name}' has been successfully updated: {changes_text}."

    @staticmethod
    async def delete_learning_objective(
        context: ConversationContext,
        objective_id: str,
    ) -> Tuple[bool, Optional[str]]:
        """Delete a learning objective by ID."""
        share_id = await ShareManager.get_share_id(context)
        if not share_id:
            logger.error("Cannot delete learning objective: no share associated with this conversation")
            return False, "No share associated with this conversation."

        current_user_id = await require_current_user(context, "delete learning objective")
        if not current_user_id:
            return False, "Could not identify current user."

        share = ShareStorage.read_share(share_id)
        if not share or not share.learning_objectives:
            return False, "No learning objectives found."

        # Find objective by ID
        objective = None
        objective_index = -1
        for idx, obj in enumerate(share.learning_objectives):
            if obj.id == objective_id:
                objective = obj
                objective_index = idx
                break

        if not objective:
            available_ids = [obj.id for obj in share.learning_objectives]
            return False, f"Learning objective with ID '{objective_id}' not found. Available objective IDs: {', '.join(available_ids[:3]) + ('...' if len(available_ids) > 3 else '')}"

        objective_name = objective.name

        # Clean up any achievement records for all outcomes in this objective across all team conversations
        for outcome in objective.learning_outcomes:
            for team_info in share.team_conversations.values():
                team_info.outcome_achievements = [
                    achievement for achievement in team_info.outcome_achievements
                    if achievement.outcome_id != outcome.id
                ]

        # Remove the objective from the share
        share.learning_objectives.pop(objective_index)

        ShareStorage.write_share(share_id, share)

        await ShareStorage.log_share_event(
            context=context,
            share_id=share_id,
            entry_type=LogEntryType.LEARNING_OBJECTIVE_UPDATED.value,
            message=f"Deleted learning objective '{objective_name}' and all its outcomes",
            metadata={
                "objective_id": objective_id,
                "objective_name": objective_name,
                "outcomes_count": len(objective.learning_outcomes),
            },
        )

        await Notifications.notify_all(context, share_id, f"Learning objective '{objective_name}' has been deleted")
        await Notifications.notify_all_state_update(context, share_id, [InspectorTab.LEARNING, InspectorTab.BRIEF])

        return True, f"Learning objective '{objective_name}' has been successfully deleted from the knowledge package."

    @staticmethod
    async def get_learning_outcomes(context: ConversationContext) -> List[LearningOutcome]:

        share_id = await ShareManager.get_share_id(context)
        if not share_id:
            return []

        share = ShareStorage.read_share(share_id)
        if not share:
            return []

        objectives = share.learning_objectives
        outcomes = []
        for objective in objectives:
            outcomes.extend(objective.learning_outcomes)

        return outcomes

    @staticmethod
    async def add_learning_outcome(
        context: ConversationContext,
        objective_id: str,
        outcome_description: str,
    ) -> Tuple[bool, Optional[str]]:
        """Add a new learning outcome to an existing learning objective."""
        share_id = await ShareManager.get_share_id(context)
        if not share_id:
            logger.error("Cannot add learning outcome: no share associated with this conversation")
            return False, "No knowledge package associated with this conversation."

        current_user_id = await require_current_user(context, "add learning outcome")
        if not current_user_id:
            return False, "Could not identify current user."

        share = ShareStorage.read_share(share_id)
        if not share or not share.learning_objectives:
            return False, "No learning objectives found. Please add objectives before adding outcomes."

        # Find the objective by ID
        objective = None
        for obj in share.learning_objectives:
            if obj.id == objective_id:
                objective = obj
                break

        if objective is None:
            available_ids = [obj.id for obj in share.learning_objectives]
            return False, f"Learning objective with ID '{objective_id}' not found. Available objective IDs: {', '.join(available_ids[:3]) + ('...' if len(available_ids) > 3 else '')}"

        # Create the new outcome
        new_outcome = LearningOutcome(description=outcome_description.strip())

        # Add the outcome to the objective
        objective.learning_outcomes.append(new_outcome)

        # Save the updated knowledge package
        ShareStorage.write_share(share_id, share)

        # Log the outcome addition
        await ShareStorage.log_share_event(
            context=context,
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
        await Notifications.notify_all(context, share_id, f"Learning outcome '{outcome_description}' has been added")
        await Notifications.notify_all_state_update(context, share_id, [InspectorTab.LEARNING, InspectorTab.BRIEF])

        return True, f"Learning outcome added successfully to objective '{objective.name}': {outcome_description}"

    @staticmethod
    async def update_learning_outcome(
        context: ConversationContext,
        outcome_id: str,
        new_description: str,
    ) -> Tuple[bool, Optional[str]]:
        """Update the description of an existing learning outcome."""
        share_id = await ShareManager.get_share_id(context)
        if not share_id:
            logger.error("Cannot update learning outcome: no share associated with this conversation")
            return False, "No knowledge package associated with this conversation."

        current_user_id = await require_current_user(context, "update learning outcome")
        if not current_user_id:
            return False, "Could not identify current user."

        share = ShareStorage.read_share(share_id)
        if not share or not share.learning_objectives:
            return False, "No learning objectives found. Please add objectives before updating outcomes."

        # Find the outcome by ID across all objectives
        objective = None
        outcome = None
        for obj in share.learning_objectives:
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
            for obj in share.learning_objectives:
                for out in obj.learning_outcomes:
                    available_outcome_ids.append(out.id)
            return False, f"Learning outcome with ID '{outcome_id}' not found. Available outcome IDs: {', '.join(available_outcome_ids[:3]) + ('...' if len(available_outcome_ids) > 3 else '')}"

        old_description = outcome.description

        # Update the outcome description
        outcome.description = new_description.strip()

        # Save the updated knowledge package
        ShareStorage.write_share(share_id, share)

        # Log the outcome update
        await ShareStorage.log_share_event(
            context=context,
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
        await Notifications.notify_all(context, share_id, f"Learning outcome '{new_description}' has been updated")
        await Notifications.notify_all_state_update(context, share_id, [InspectorTab.LEARNING, InspectorTab.BRIEF])

        return True, f"Learning outcome updated successfully in objective '{objective.name}': {new_description}"

    @staticmethod
    async def delete_learning_outcome(
        context: ConversationContext,
        outcome_id: str,
    ) -> Tuple[bool, Optional[str]]:
        """Delete a learning outcome from a learning objective."""
        share_id = await ShareManager.get_share_id(context)
        if not share_id:
            logger.error("Cannot delete learning outcome: no share associated with this conversation")
            return False, "No knowledge package associated with this conversation."

        current_user_id = await require_current_user(context, "delete learning outcome")
        if not current_user_id:
            return False, "Could not identify current user."

        share = ShareStorage.read_share(share_id)
        if not share or not share.learning_objectives:
            return False, "No learning objectives found. Please add objectives before deleting outcomes."

        # Find the outcome by ID across all objectives
        objective = None
        outcome_to_delete = None
        outcome_index = -1
        for obj in share.learning_objectives:
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
            for obj in share.learning_objectives:
                for out in obj.learning_outcomes:
                    available_outcome_ids.append(out.id)
            return False, f"Learning outcome with ID '{outcome_id}' not found. Available outcome IDs: {', '.join(available_outcome_ids[:3]) + ('...' if len(available_outcome_ids) > 3 else '')}"

        deleted_description = outcome_to_delete.description

        # Remove the outcome from the objective
        objective.learning_outcomes.pop(outcome_index)

        # Clean up any achievement records for this outcome across all team conversations
        for team_info in share.team_conversations.values():
            team_info.outcome_achievements = [
                achievement for achievement in team_info.outcome_achievements
                if achievement.outcome_id != outcome_id
            ]

        # Save the updated knowledge package
        ShareStorage.write_share(share_id, share)

        # Log the outcome deletion
        await ShareStorage.log_share_event(
            context=context,
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
        await Notifications.notify_all(context, share_id, f"Learning outcome '{deleted_description}' has been removed")
        await Notifications.notify_all_state_update(context, share_id, [InspectorTab.LEARNING, InspectorTab.BRIEF])

        return True, f"Learning outcome deleted successfully from objective '{objective.name}': {deleted_description}"
