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
    LogEntryType,
)
from assistant.domain import LearningObjectivesManager, ShareManager
from assistant.logging import logger
from assistant.notifications import Notifications
from assistant.utils import get_current_user_id

from .base import ToolsBase


class ProgressTrackingTools(ToolsBase):
    """Tools for tracking learning progress."""

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
            await Notifications.notify_all_state_update(self.context, [InspectorTab.BRIEF])

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
