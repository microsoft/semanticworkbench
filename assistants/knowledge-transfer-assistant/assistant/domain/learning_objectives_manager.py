"""
Learning objectives and outcomes management for Knowledge Transfer Assistant.

Handles learning objectives, outcomes creation, updates, and deletion.
"""

from typing import List, Optional, Tuple

from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant.data import (
    InspectorTab,
    KnowledgePackage,
    LearningObjective,
    LearningOutcome,
    LearningOutcomeAchievement,
    LogEntryType,
)
from assistant.notifications import Notifications

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

        share = await ShareManager.get_share(context)

        share.learning_objectives.append(new_learning_objective)

        await ShareManager.set_share(context, share)

        await ShareManager.log_share_event(
            context=context,
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
    ) -> str:
        """
        Update an existing learning objective's name or description.

        Returns:
            Success message
        """
        share = await ShareManager.get_share(context)
        if not share.learning_objectives:
            raise ValueError("No learning objectives found")

        # Find objective by ID
        objective = None
        for obj in share.learning_objectives:
            if obj.id == objective_id:
                objective = obj
                break

        if not objective:
            available_ids = [obj.id for obj in share.learning_objectives]
            raise ValueError(
                f"Learning objective with ID '{objective_id}' not found. Available objective IDs: {', '.join(available_ids[:3]) + ('...' if len(available_ids) > 3 else '')}"
            )

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
            return "No changes specified"

        await ShareManager.set_share(context, share)

        changes_text = ", ".join(changes_made)
        await ShareManager.log_share_event(
            context=context,
            entry_type=LogEntryType.LEARNING_OBJECTIVE_UPDATED.value,
            message=f"Updated learning objective '{objective.name}': {changes_text}",
            metadata={
                "objective_id": objective_id,
                "objective_name": objective.name,
                "changes": changes_text,
            },
        )

        await Notifications.notify_all(
            context, share.share_id, f"Learning objective '{objective.name}' has been updated"
        )
        await Notifications.notify_all_state_update(
            context, share.share_id, [InspectorTab.LEARNING, InspectorTab.BRIEF]
        )

        return f"Learning objective '{objective.name}' has been successfully updated: {changes_text}."

    @staticmethod
    async def delete_learning_objective(
        context: ConversationContext,
        objective_id: str,
    ) -> str:
        """
        Delete a learning objective by ID.

        Returns:
            Success message
        """
        share = await ShareManager.get_share(context)
        if not share.learning_objectives:
            raise ValueError("No learning objectives found")

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
            raise ValueError(
                f"Learning objective with ID '{objective_id}' not found. Available objective IDs: {', '.join(available_ids[:3]) + ('...' if len(available_ids) > 3 else '')}"
            )

        objective_name = objective.name

        # Clean up any achievement records for all outcomes in this objective across all team conversations
        for outcome in objective.learning_outcomes:
            for team_info in share.team_conversations.values():
                team_info.outcome_achievements = [
                    achievement
                    for achievement in team_info.outcome_achievements
                    if achievement.outcome_id != outcome.id
                ]

        # Remove the objective from the share
        share.learning_objectives.pop(objective_index)

        await ShareManager.set_share(context, share)

        await ShareManager.log_share_event(
            context=context,
            entry_type=LogEntryType.LEARNING_OBJECTIVE_UPDATED.value,
            message=f"Deleted learning objective '{objective_name}' and all its outcomes",
            metadata={
                "objective_id": objective_id,
                "objective_name": objective_name,
                "outcomes_count": len(objective.learning_outcomes),
            },
        )

        await Notifications.notify_all(
            context, share.share_id, f"Learning objective '{objective_name}' has been deleted"
        )
        await Notifications.notify_all_state_update(
            context, share.share_id, [InspectorTab.LEARNING, InspectorTab.BRIEF]
        )

        return f"Learning objective '{objective_name}' has been successfully deleted from the knowledge package."

    @staticmethod
    async def get_learning_outcomes(
        context: ConversationContext,
    ) -> List[LearningOutcome]:
        share = await ShareManager.get_share(context)

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
    ) -> str:
        """
        Add a new learning outcome to an existing learning objective.

        Returns:
            Success message
        """
        share = await ShareManager.get_share(context)
        if not share.learning_objectives:
            raise ValueError("No learning objectives found. Please add objectives before adding outcomes.")

        # Find the objective by ID
        objective = None
        for obj in share.learning_objectives:
            if obj.id == objective_id:
                objective = obj
                break

        if objective is None:
            available_ids = [obj.id for obj in share.learning_objectives]
            raise ValueError(
                f"Learning objective with ID '{objective_id}' not found. Available objective IDs: {', '.join(available_ids[:3]) + ('...' if len(available_ids) > 3 else '')}"
            )

        # Create the new outcome
        new_outcome = LearningOutcome(description=outcome_description.strip())

        # Add the outcome to the objective
        objective.learning_outcomes.append(new_outcome)

        # Save the updated knowledge package
        await ShareManager.set_share(context, share)

        # Log the outcome addition
        await ShareManager.log_share_event(
            context=context,
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
        await Notifications.notify_all(
            context,
            share.share_id,
            f"Learning outcome '{outcome_description}' has been added",
        )
        await Notifications.notify_all_state_update(
            context, share.share_id, [InspectorTab.LEARNING, InspectorTab.BRIEF]
        )

        return f"Learning outcome added successfully to objective '{objective.name}': {outcome_description}"

    @staticmethod
    async def update_learning_outcome(
        context: ConversationContext,
        outcome_id: str,
        new_description: str,
    ) -> str:
        """
        Update the description of an existing learning outcome.

        Returns:
            Success message
        """
        share = await ShareManager.get_share(context)
        if not share.learning_objectives:
            raise ValueError("No learning objectives found. Please add objectives before updating outcomes.")

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
            raise ValueError(
                f"Learning outcome with ID '{outcome_id}' not found. Available outcome IDs: {', '.join(available_outcome_ids[:3]) + ('...' if len(available_outcome_ids) > 3 else '')}"
            )

        old_description = outcome.description

        # Update the outcome description
        outcome.description = new_description.strip()

        # Save the updated knowledge package
        await ShareManager.set_share(context, share)

        # Log the outcome update
        await ShareManager.log_share_event(
            context=context,
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
        await Notifications.notify_all(
            context, share.share_id, f"Learning outcome '{new_description}' has been updated"
        )
        await Notifications.notify_all_state_update(
            context, share.share_id, [InspectorTab.LEARNING, InspectorTab.BRIEF]
        )

        return f"Learning outcome updated successfully in objective '{objective.name}': {new_description}"

    @staticmethod
    async def delete_learning_outcome(
        context: ConversationContext,
        outcome_id: str,
    ) -> str:
        """
        Delete a learning outcome from a learning objective.

        Returns:
            Success message
        """
        share = await ShareManager.get_share(context)
        if not share.learning_objectives:
            raise ValueError("No learning objectives found. Please add objectives before deleting outcomes.")

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
            raise ValueError(
                f"Learning outcome with ID '{outcome_id}' not found. Available outcome IDs: {', '.join(available_outcome_ids[:3]) + ('...' if len(available_outcome_ids) > 3 else '')}"
            )

        deleted_description = outcome_to_delete.description

        # Remove the outcome from the objective
        objective.learning_outcomes.pop(outcome_index)

        # Clean up any achievement records for this outcome across all team conversations
        for team_info in share.team_conversations.values():
            team_info.outcome_achievements = [
                achievement for achievement in team_info.outcome_achievements if achievement.outcome_id != outcome_id
            ]

        # Save the updated knowledge package
        await ShareManager.set_share(context, share)

        # Log the outcome deletion
        await ShareManager.log_share_event(
            context=context,
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
        await Notifications.notify_all(
            context,
            share.share_id,
            f"Learning outcome '{deleted_description}' has been removed",
        )
        await Notifications.notify_all_state_update(
            context, share.share_id, [InspectorTab.LEARNING, InspectorTab.BRIEF]
        )

        return f"Learning outcome deleted successfully from objective '{objective.name}': {deleted_description}"

    @staticmethod
    def get_achievements_for_conversation(
        package: KnowledgePackage, conversation_id: str
    ) -> List[LearningOutcomeAchievement]:
        team_conv = package.team_conversations.get(conversation_id)
        return team_conv.outcome_achievements if team_conv else []

    @staticmethod
    def get_completion_for_conversation(package: KnowledgePackage, conversation_id: str) -> Tuple[int, int]:
        achievements = LearningObjectivesManager.get_achievements_for_conversation(package, conversation_id)
        achieved_outcome_ids = {a.outcome_id for a in achievements if a.achieved}

        total_outcomes = sum(len(obj.learning_outcomes) for obj in package.learning_objectives)
        achieved_outcomes = len(achieved_outcome_ids)

        return achieved_outcomes, total_outcomes

    @staticmethod
    def is_outcome_achieved_by_conversation(package: KnowledgePackage, outcome_id: str, conversation_id: str) -> bool:
        achievements = LearningObjectivesManager.get_achievements_for_conversation(package, conversation_id)
        return any(a.outcome_id == outcome_id and a.achieved for a in achievements)

    @staticmethod
    def get_overall_completion(package: KnowledgePackage) -> Tuple[int, int]:
        """
        Get overall completion across all team conversations.
        Returns:
            Tuple of (unique_achieved_outcomes, total_outcomes) across all team conversations
        """
        all_achieved_outcomes = set()
        for team_conv in package.team_conversations.values():
            achieved_ids = {a.outcome_id for a in team_conv.outcome_achievements if a.achieved}
            all_achieved_outcomes.update(achieved_ids)

        total_outcomes = sum(len(obj.learning_outcomes) for obj in package.learning_objectives)
        return len(all_achieved_outcomes), total_outcomes
