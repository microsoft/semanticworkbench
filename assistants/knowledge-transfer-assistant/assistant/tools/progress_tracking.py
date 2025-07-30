"""
Progress tracking tools for Knowledge Transfer Assistant.

Tools for tracking learning progress and completing knowledge transfer activities.
"""

from datetime import UTC, datetime

from semantic_workbench_api_model.workbench_model import (
    MessageType,
    NewConversationMessage,
)

from assistant.data import (
    InspectorTab,
    LearningOutcomeAchievement,
    LogEntryType,
)
from assistant.domain import LearningObjectivesManager, ShareManager, TransferManager
from assistant.logging import logger
from assistant.notifications import Notifications
from assistant.utils import get_current_user_id

from .base import ToolsBase


class ProgressTrackingTools(ToolsBase):
    """Tools for tracking learning progress."""

    async def mark_learning_outcome_achieved(self, objective_id: str, outcome_id: str) -> str:
        """
        Mark a learning outcome as achieved for tracking knowledge transfer progress.

        WHEN TO USE:
        - When the user reports completing a specific learning task or deliverable
        - When evidence has been provided that a learning outcome has been met
        - When a milestone for one of the learning objectives has been achieved
        - When tracking progress and updating the transfer status

        Each completed outcome moves the knowledge transfer closer to completion. When all outcomes are achieved, the transfer can be marked as complete.

        Args:
            objective_id: The UUID of the learning objective
            outcome_id: The UUID of the learning outcome within the objective

        Returns:
            A message indicating success or failure
        """  # noqa: E501
        try:
            share = await ShareManager.get_share(self.context)
            brief = share.brief
            if not brief:
                return "No knowledge brief found."

            # Find the objective by ID
            objective = None
            for obj in share.learning_objectives:
                if obj.id == objective_id:
                    objective = obj
                    break
            if not objective:
                return f"Learning objective with ID '{objective_id}' not found."

            # Find the outcome by ID within the objective
            outcome = None
            for out in objective.learning_outcomes:
                if out.id == outcome_id:
                    outcome = out
                    break

            if not outcome:
                return f"Learning outcome with ID '{outcome_id}' not found in objective '{objective.name}'."

            conversation_id = str(self.context.id)

            # Check if already achieved by this conversation
            if LearningObjectivesManager.is_outcome_achieved_by_conversation(share, outcome.id, conversation_id):
                return f"Outcome '{outcome.description}' is already marked as achieved by this team member."

            # Ensure team conversation info exists
            if conversation_id not in share.team_conversations:
                return "Team conversation not properly registered. Please contact the coordinator."

            # Create achievement record
            achievement = LearningOutcomeAchievement(
                outcome_id=outcome.id, achieved=True, achieved_at=datetime.now(UTC)
            )

            # Add achievement to team conversation's achievements
            share.team_conversations[conversation_id].outcome_achievements.append(achievement)

            # Update team conversation's last active timestamp
            share.team_conversations[conversation_id].last_active_at = datetime.now(UTC)

            # Update metadata
            current_user_id = await get_current_user_id(self.context)
            share.updated_at = datetime.now(UTC)
            share.updated_by = current_user_id
            share.version += 1

            # Save the updated knowledge package
            await ShareManager.set_share(self.context, share)

            # Log the outcome achievement
            await ShareManager.log_share_event(
                context=self.context,
                entry_type=LogEntryType.OUTCOME_ATTAINED.value,
                message=f"Learning outcome achieved: {outcome.description}",
                related_entity_id=None,
                metadata={
                    "objective_name": objective.name,
                    "outcome_description": outcome.description,
                },
            )

            # Notify linked conversations with a message
            await Notifications.notify_all(
                self.context,
                share.share_id,
                f"Learning outcome '{outcome.description}' for objective '{objective.name}' has been achieved.",
            )
            await Notifications.notify_all_state_update(
                self.context,
                share.share_id,
                [InspectorTab.LEARNING, InspectorTab.BRIEF],
            )

            # Check if all outcomes are achieved for transfer completion
            # Get the knowledge package to check completion status
            if TransferManager._is_transfer_complete(share):
                await self.context.send_messages(
                    NewConversationMessage(
                        content="🎉 All learning outcomes have been achieved! The knowledge transfer has been automatically marked as complete.",  # noqa: E501
                        message_type=MessageType.notice,
                    )
                )

            await self.context.send_messages(
                NewConversationMessage(
                    content=f"Learning outcome '{outcome.description}' for objective '{objective.name}' has been marked as achieved.",  # noqa: E501
                    message_type=MessageType.notice,
                )
            )

            return f"Learning outcome '{outcome.description}' for objective '{objective.name}' marked as achieved."

        except Exception as e:
            logger.exception(f"Error marking learning outcome as achieved: {e}")
            return "An error occurred while marking the learning outcome as achieved. Please try again later."

    async def report_transfer_completion(self) -> str:
        """
        Report that the knowledge transfer is complete, concluding the transfer lifecycle.

        WHEN TO USE:
        - When all learning outcomes for all objectives have been marked as achieved
        - When the user confirms the knowledge has been successfully learned
        - When the learning objectives have been fully achieved
        - When it's time to formally conclude the knowledge transfer

        This is a significant milestone that indicates the knowledge transfer has successfully achieved all its learning objectives. Before using this tool, verify that all learning outcomes have been marked as achieved.

        Returns:
            A message indicating success or failure
        """  # noqa: E501
        try:
            share = await ShareManager.get_share(self.context)

            # Check if all outcomes are achieved
            achieved_outcomes, total_outcomes = LearningObjectivesManager.get_overall_completion(share)
            if achieved_outcomes < total_outcomes:
                remaining = total_outcomes - achieved_outcomes
                return (
                    f"Cannot complete knowledge transfer - {remaining} learning outcomes are still pending achievement."
                )

            current_user_id = await get_current_user_id(self.context)
            share.updated_at = datetime.now(UTC)
            share.updated_by = current_user_id
            share.version += 1
            await ShareManager.set_share(self.context, share)

            # Log the milestone transition
            await ShareManager.log_share_event(
                context=self.context,
                entry_type=LogEntryType.SHARE_COMPLETED.value,
                message="Transfer marked as COMPLETED",
                metadata={"milestone": "transfer_completed"},
            )

            # Notify linked conversations with a message
            await Notifications.notify_all(
                self.context,
                share.share_id,
                "🎉 **Knowledge Transfer Complete**: Team has reported that all learning objectives have been achieved. The knowledge transfer is now complete.",  # noqa: E501
            )
            await Notifications.notify_all_state_update(self.context, share.share_id, [InspectorTab.BRIEF])

            await self.context.send_messages(
                NewConversationMessage(
                    content="🎉 **Knowledge Transfer Complete**: All learning objectives have been achieved and the knowledge transfer is now complete. The Coordinator has been notified.",  # noqa: E501
                    message_type=MessageType.chat,
                )
            )

            return "Knowledge transfer successfully marked as complete. All participants have been notified."

        except Exception as e:
            logger.exception(f"Error reporting transfer completion: {e}")
            return "An error occurred while reporting transfer completion. Please try again later."
