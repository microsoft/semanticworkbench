"""
Project setup tools for Knowledge Transfer Assistant.

Tools for configuring knowledge shares.
"""

from datetime import UTC, datetime

from assistant import agentic
from assistant.data import InspectorTab
from assistant.domain.audience_manager import AudienceManager
from assistant.domain.knowledge_brief_manager import KnowledgeBriefManager
from assistant.domain.share_manager import ShareManager
from assistant.notifications import Notifications

from .base import ToolsBase


class ShareSetupTools(ToolsBase):
    """Tools for the knowledge transfer setup and configuration."""

    async def update_audience(self, audience_description: str) -> str:
        """
        Update the target audience description for this knowledge transfer.

        Args:
            audience_description: Description of the intended audience and their existing knowledge level

        Returns:
            A message indicating success or failure
        """
        try:
            await AudienceManager.update_audience(
                context=self.context,
                audience_description=audience_description,
            )
            await Notifications.notify(self.context, "Audience updated.")
            await Notifications.notify_all_state_update(self.context, [InspectorTab.DEBUG])
            return "Audience updated successfully"
        except Exception as e:
            return f"Failed to update audience: {e!s}"

    async def update_audience_takeaways(self, takeaways: list[str]) -> str:
        """
        Update the key takeaways for the target audience.

        Args:
            takeaways: List of key takeaways for the audience. Takeaways should be concise and directly related to the audience and what the user wants them to learn or understand.

        Returns:
            A message indicating success or failure
        """  # noqa: E501
        try:
            await AudienceManager.update_audience_takeaways(
                context=self.context,
                takeaways=takeaways,
            )
            await Notifications.notify(self.context, "Audience takeaways updated.")
            await Notifications.notify_all_state_update(self.context, [InspectorTab.BRIEF])
            return "Audience takeaways updated successfully"
        except Exception as e:
            return f"Failed to update audience takeaways: {e!s}"

    # async def set_knowledge_organized(self, is_organized: bool) -> str:
    #     """
    #     Mark that all necessary knowledge has been captured and organized for transfer.

    #     This indicates that the coordinator has uploaded files, shared information through conversation, and confirmed that all necessary knowledge for the transfer has been captured. This is required before the knowledge package can move to the "Ready for Transfer" state. # noqa: E501

    #     Args:
    #         is_organized: True if knowledge is organized and ready, False to
    #         mark as currently unorganized

    #     Returns:
    #         A message indicating success or failure
    #     """
    #     try:
    #         share = await ShareManager.get_share(self.context)
    #         share.knowledge_organized = is_organized
    #         share.updated_at = datetime.now(UTC)
    #         await ShareManager.set_share(self.context, share)

    #         if is_organized:
    #             guidance = "Knowledge is now marked as organized and ready. You can proceed to create your brief and set up learning objectives."  # noqa: E501
    #         else:
    #             guidance = "Knowledge is now marked as incomplete. Continue organizing your knowledge by uploading files or describing it in conversation."  # noqa: E501
    #         return f"Knowledge organization status updated successfully. {guidance}"

    #     except Exception as e:
    #         return f"Failed to update knowledge organization status: {e!s}"

    async def update_brief(self, title: str, description: str) -> str:
        """
        Update a brief with a title and description. The brief should avoid
        filler words and unnecessary content.

        Args:
            title: The title of the brief description: A description of the
            knowledge share to be given to recipients as context.

        Returns:
            A message indicating success or failure
        """
        try:
            await KnowledgeBriefManager.update_knowledge_brief(
                context=self.context,
                title=title,
                description=description,
            )
            return "Brief updated successfully."
        except Exception as e:
            return f"Failed to update brief: {e!s}"

    async def set_learning_intention(self, is_for_specific_outcomes: bool) -> str:
        """
        Set or update whether this knowledge package is intended for specific learning outcomes or general exploration.  If intended for learning and an objective or outcome was provided, you should run the add_learning_objective function next (don't wait).

        Args:
            is_for_specific_outcomes: True if this package should have learning
            objectives and outcomes, False if this is for general exploration

        Returns:
            A message indicating success or failure
        """  # noqa: E501
        try:
            share = await ShareManager.get_share(self.context)
            share.is_intended_to_accomplish_outcomes = is_for_specific_outcomes
            share.updated_at = datetime.now(UTC)
            await ShareManager.set_share(self.context, share)
            await Notifications.notify(self.context, "Knowledge share learning intention set.")

            # Provide appropriate guidance based on the choice
            if is_for_specific_outcomes:
                guidance = "This knowledge package is now set for specific learning outcomes. You'll need to add learning objectives with measurable outcomes."  # noqa: E501
            else:
                guidance = "This knowledge package is now set for general exploration. No specific learning objectives are required."  # noqa: E501

            return f"Learning intention updated successfully. {guidance}"

        except Exception as e:
            return f"Failed to update learning intention: {e!s}"

    async def create_invitation(self) -> str:
        """
        Create an invitation for the knowledge transfer.

        Args:
            invitation_text: The text of the invitation to be sent to participants.

        Returns:
            A message indicating success or failure
        """
        try:
            invitation = await agentic.create_invitation(self.context)
            return invitation
        except Exception as e:
            return f"Failed to create invitation: {e!s}"
