"""
Learning objectives management tools for Knowledge Transfer Assistant.

Tools for creating, updating, and managing learning objectives and outcomes.
"""

from assistant.domain import LearningObjectivesManager
from assistant.logging import logger

from .base import ToolsBase


class LearningObjectiveTools(ToolsBase):
    """Tools for managing learning objectives and outcomes."""

    async def add_learning_objective(self, objective_name: str, description: str, learning_outcomes: list[str]) -> str:
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
        objective = await LearningObjectivesManager.add_learning_objective(
            context=self.context,
            objective_name=objective_name,
            description=description,
            outcomes=learning_outcomes,
        )

        if objective:
            return f"Learning objective '{objective_name}' added to knowledge brief successfully."
        else:
            return "Failed to add learning objective. Please try again."

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
        try:
            message = await LearningObjectivesManager.update_learning_objective(
                context=self.context,
                objective_id=objective_id,
                objective_name=objective_name if objective_name.strip() else None,
                description=description if description.strip() else None,
            )
            return message
        except Exception as e:
            logger.exception(f"Failed to update learning objective: {e}")
            return f"Failed to update learning objective: {e!s}"

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
        try:
            message = await LearningObjectivesManager.delete_learning_objective(
                context=self.context,
                objective_id=objective_id,
            )
            return message
        except Exception as e:
            logger.exception(f"Failed to delete learning objective: {e}")
            return f"Failed to delete learning objective: {e!s}"
