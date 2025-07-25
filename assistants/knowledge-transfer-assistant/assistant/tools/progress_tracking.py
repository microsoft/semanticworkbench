"""
Progress tracking tools for Knowledge Transfer Assistant.

Tools for tracking learning progress and completing knowledge transfer activities.
"""

from datetime import datetime

from semantic_workbench_api_model.workbench_model import (
    MessageType,
    NewConversationMessage,
)

from ..data import InspectorTab, LearningOutcomeAchievement, LogEntryType
from assistant.domain import KnowledgeTransferManager
from assistant.notifications import Notifications
from assistant.storage import ShareStorage
from assistant.storage_models import ConversationRole
from .base import ToolsBase


class ProgressTrackingTools(ToolsBase):
    """Tools for tracking learning progress."""

    async def mark_learning_outcome_achieved(self, objective_index: int, criterion_index: int) -> str:
        """
        Mark a learning outcome as achieved for tracking knowledge transfer progress.

        WHEN TO USE:
        - When the user reports completing a specific learning task or deliverable
        - When evidence has been provided that a learning outcome has been met
        - When a milestone for one of the learning objectives has been achieved
        - When tracking progress and updating the transfer status

        Each completed outcome moves the knowledge transfer closer to completion. When all outcomes
        are achieved, the transfer can be marked as complete.

        IMPORTANT: Always use get_share_info() first to see the current objectives, outcomes, and their indices
        before marking anything as complete.

        Args:
            objective_index: The index of the objective (0-based integer) from get_share_info() output
            criterion_index: The index of the outcome within the objective (0-based integer)

        Returns:
            A message indicating success or failure
        """

        if self.role is not ConversationRole.TEAM:
            return "Only Team members can mark criteria as completed."

        # Get share ID
        share_id = await KnowledgeTransferManager.get_share_id(self.context)
        if not share_id:
            return "No knowledge package associated with this conversation. Unable to mark outcome as achieved."

        # Get existing knowledge brief
        brief = await KnowledgeTransferManager.get_knowledge_brief(self.context)
        if not brief:
            return "No knowledge brief found."

        # Using 0-based indexing directly, no adjustment needed

        # Get the knowledge package to access objectives
        knowledge_package = ShareStorage.read_share(share_id)
        if not knowledge_package or not knowledge_package.learning_objectives:
            return "No learning objectives found."

        # Validate indices
        if objective_index < 0 or objective_index >= len(knowledge_package.learning_objectives):
            return f"Invalid objective index {objective_index}. Valid indexes are 0 to {len(knowledge_package.learning_objectives) - 1}. There are {len(knowledge_package.learning_objectives)} objectives."

        objective = knowledge_package.learning_objectives[objective_index]

        if criterion_index < 0 or criterion_index >= len(objective.learning_outcomes):
            return f"Invalid outcome index {criterion_index}. Valid indexes for objective '{objective.name}' are 0 to {len(objective.learning_outcomes) - 1}. Objective '{objective.name}' has {len(objective.learning_outcomes)} outcomes."

        # Update the outcome
        outcome = objective.learning_outcomes[criterion_index]
        conversation_id = str(self.context.id)

        # Check if already achieved by this conversation
        if knowledge_package.is_outcome_achieved_by_conversation(outcome.id, conversation_id):
            return f"Outcome '{outcome.description}' is already marked as achieved by this team member."

        # Get current user information
        participants = await self.context.get_participants()
        current_user_id = None

        for participant in participants.participants:
            if participant.role == "user":
                current_user_id = participant.id
                break

        if not current_user_id:
            return "Could not identify current user."

        # Ensure team conversation info exists
        if conversation_id not in knowledge_package.team_conversations:
            return "Team conversation not properly registered. Please contact the coordinator."

        # Create achievement record
        achievement = LearningOutcomeAchievement(outcome_id=outcome.id, achieved=True, achieved_at=datetime.utcnow())

        # Add achievement to team conversation's achievements
        knowledge_package.team_conversations[conversation_id].outcome_achievements.append(achievement)

        # Update team conversation's last active timestamp
        knowledge_package.team_conversations[conversation_id].last_active_at = datetime.utcnow()

        # Save the updated knowledge package with the achieved outcome
        ShareStorage.write_share(share_id, knowledge_package)

        # Log the outcome achievement
        await ShareStorage.log_share_event(
            context=self.context,
            share_id=share_id,
            entry_type=LogEntryType.OUTCOME_ATTAINED.value,
            message=f"Learning outcome achieved: {outcome.description}",
            related_entity_id=None,
            metadata={"objective_name": objective.name, "outcome_description": outcome.description},
        )

        # Update knowledge package
        knowledge_package = ShareStorage.read_share(share_id)

        if knowledge_package:
            # Update metadata
            knowledge_package.updated_at = datetime.utcnow()
            knowledge_package.updated_by = current_user_id
            knowledge_package.version += 1

            # Save the updated knowledge package
            ShareStorage.write_share(share_id, knowledge_package)

            # Notify linked conversations with a message
            await Notifications.notify_all(
                self.context,
                share_id,
                f"Learning outcome '{outcome.description}' for objective '{objective.name}' has been marked as achieved.",
            )
            await Notifications.notify_all_state_update(
                self.context, share_id, [InspectorTab.LEARNING, InspectorTab.BRIEF]
            )

            # Update all share UI inspectors
            await ShareStorage.refresh_all_share_uis(
                self.context, share_id, [InspectorTab.LEARNING, InspectorTab.BRIEF]
            )

            # Check if all outcomes are achieved for transfer completion
            # Get the knowledge package to check completion status
            knowledge_package = ShareStorage.read_share(share_id)
            if knowledge_package and knowledge_package._is_transfer_complete():
                await self.context.send_messages(
                    NewConversationMessage(
                        content="🎉 All learning outcomes have been achieved! The knowledge transfer has been automatically marked as complete.",
                        message_type=MessageType.notice,
                    )
                )

        await self.context.send_messages(
            NewConversationMessage(
                content=f"Learning outcome '{outcome.description}' for objective '{objective.name}' has been marked as achieved.",
                message_type=MessageType.notice,
            )
        )

        return f"Learning outcome '{outcome.description}' for objective '{objective.name}' marked as achieved."

    async def report_transfer_completion(self) -> str:
        """
        Report that the knowledge transfer is complete, concluding the transfer lifecycle.

        WHEN TO USE:
        - When all learning outcomes for all objectives have been marked as achieved
        - When the user confirms the knowledge has been successfully learned
        - When the learning objectives have been fully achieved
        - When it's time to formally conclude the knowledge transfer

        This is a significant milestone that indicates the knowledge transfer has successfully
        achieved all its learning objectives. Before using this tool, verify that all learning outcomes
        have been marked as achieved.

        Returns:
            A message indicating success or failure
        """

        if self.role is not ConversationRole.TEAM:
            return "Only Team members can report knowledge transfer completion."

        share_id = await KnowledgeTransferManager.get_share_id(self.context)
        if not share_id:
            return "No knowledge package associated with this conversation. Unable to report transfer completion."

        package = ShareStorage.read_share(share_id)
        if not package:
            return "No knowledge package found. Cannot complete transfer without package information."

        # Check if all outcomes are achieved
        achieved_outcomes, total_outcomes = package.get_overall_completion()
        if achieved_outcomes < total_outcomes:
            remaining = total_outcomes - achieved_outcomes
            return f"Cannot complete knowledge transfer - {remaining} learning outcomes are still pending achievement."

        # Get current user information
        participants = await self.context.get_participants()
        current_user_id = None

        for participant in participants.participants:
            if participant.role == "user":
                current_user_id = participant.id
                break

        if not current_user_id:
            return "Could not identify current user."

        package.updated_at = datetime.utcnow()
        package.updated_by = current_user_id
        package.version += 1
        ShareStorage.write_share(share_id, package)

        # Log the milestone transition
        await ShareStorage.log_share_event(
            context=self.context,
            share_id=share_id,
            entry_type=LogEntryType.SHARE_COMPLETED.value,
            message="Transfer marked as COMPLETED",
            metadata={"milestone": "transfer_completed"},
        )

        # Notify linked conversations with a message
        await Notifications.notify_all(
            self.context,
            share_id,
            "🎉 **Knowledge Transfer Complete**: Team has reported that all learning objectives have been achieved. The knowledge transfer is now complete.",
        )
        await Notifications.notify_all_state_update(self.context, share_id, [InspectorTab.BRIEF])

        await ShareStorage.refresh_all_share_uis(self.context, share_id, [InspectorTab.BRIEF])

        await self.context.send_messages(
            NewConversationMessage(
                content="🎉 **Knowledge Transfer Complete**: All learning objectives have been achieved and the knowledge transfer is now complete. The Coordinator has been notified.",
                message_type=MessageType.chat,
            )
        )

        return "Knowledge transfer successfully marked as complete. All participants have been notified."
