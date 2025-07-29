"""
Learning outcomes management tools for Knowledge Transfer Assistant.

Tools for managing individual learning outcomes within objectives.
"""

from assistant.domain import LearningObjectivesManager
from assistant.logging import logger

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
        try:
            message = await LearningObjectivesManager.add_learning_outcome(
                context=self.context,
                objective_id=objective_id,
                outcome_description=outcome_description,
            )
            return message
        except Exception as e:
            logger.exception(f"Failed to add learning outcome: {e}")
            return f"Failed to add learning outcome: {str(e)}"

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
        try:
            message = await LearningObjectivesManager.update_learning_outcome(
                context=self.context,
                outcome_id=outcome_id,
                new_description=new_description,
            )
            return message
        except Exception as e:
            logger.exception(f"Failed to update learning outcome: {e}")
            return f"Failed to update learning outcome: {str(e)}"

    async def delete_learning_outcome(self, outcome_id: str) -> str:
        """
        Delete a learning outcome from a learning objective.

        WHEN TO USE:
        - When an outcome is no longer relevant or necessary
        - When consolidating redundant outcomes
        - When removing outcomes that were added by mistake
        - When simplifying objectives by removing overly specific outcomes

        NOTE: This action is irreversible.

        Args:
            outcome_id: The unique ID of the learning outcome to delete

        Returns:
            A message indicating success or failure
        """
        try:
            message = await LearningObjectivesManager.delete_learning_outcome(
                context=self.context,
                outcome_id=outcome_id,
            )
            return message
        except Exception as e:
            logger.exception(f"Failed to delete learning outcome: {e}")
            return f"Failed to delete learning outcome: {str(e)}"
