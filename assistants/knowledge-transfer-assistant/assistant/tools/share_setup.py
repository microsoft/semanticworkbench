"""
Project setup tools for Knowledge Transfer Assistant.

Tools for initializing and configuring knowledge packages.
"""

from datetime import datetime

from assistant.domain import KnowledgeTransferManager
from assistant.storage import ShareStorage
from assistant.data import ConversationRole
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
        if self.role is not ConversationRole.COORDINATOR:
            return "Only Coordinator can update the audience description."

        success, message = await KnowledgeTransferManager.update_audience(
            context=self.context,
            audience_description=audience_description,
        )

        return message if message else ("Audience updated successfully." if success else "Failed to update audience.")

    async def set_knowledge_organized(self, is_organized: bool) -> str:
        """
        Mark that all necessary knowledge has been captured and organized for transfer.

        This indicates that the coordinator has uploaded files, shared information through conversation,
        and confirmed that all necessary knowledge for the transfer has been captured. This is required
        before the knowledge package can move to the "Ready for Transfer" state.

        Args:
            is_organized: True if knowledge is organized and ready, False to mark as currently unorganized

        Returns:
            A message indicating success or failure
        """
        if self.role is not ConversationRole.COORDINATOR:
            return "Only Coordinator can mark knowledge as organized."

        # Get share ID
        share_id = await KnowledgeTransferManager.get_share_id(self.context)
        if not share_id:
            return "No knowledge package associated with this conversation."

        # Get existing knowledge package
        package = ShareStorage.read_share(share_id)
        if not package:
            return "No knowledge package found. Please create a knowledge brief first."

        # Update the knowledge organized flag
        package.knowledge_organized = is_organized
        package.updated_at = datetime.utcnow()

        # Save the updated package
        ShareStorage.write_share(share_id, package)

        # Provide appropriate feedback
        if is_organized:
            guidance = "Knowledge is now marked as organized and ready. You can proceed to create your brief and set up learning objectives."
        else:
            guidance = "Knowledge is now marked as incomplete. Continue organizing your knowledge by uploading files or describing it in conversation."

        return f"Knowledge organization status updated successfully. {guidance}"

    async def update_brief(self, title: str, description: str) -> str:
        """
        Update a brief with a title and description. The brief should avoid filler words and unnecessary content.

        Args:
            title: The title of the brief
            description: A description of the knowledge share to be given to recipients as context.

        Returns:
            A message indicating success or failure
        """
        if self.role is not ConversationRole.COORDINATOR:
            return "Only Coordinator can create knowledge briefs."

        share_id = await KnowledgeTransferManager.get_share_id(self.context)
        if not share_id:
            return "No knowledge package associated with this conversation. Please create a knowledge package first."

        brief = await KnowledgeTransferManager.update_knowledge_brief(
            context=self.context,
            title=title,
            description=description,
        )

        if brief:
            return f"Brief '{title}' updated successfully."
        else:
            return "Failed to update the brief. Please try again."

    async def set_learning_intention(self, is_for_specific_outcomes: bool) -> str:
        """
        Set or update whether this knowledge package is intended for specific learning outcomes or general exploration.  If intended for learning and an objective or outcome was provided, you should run the add_learning_objective function next (don't wait).

        Args:
            is_for_specific_outcomes: True if this package should have learning objectives and outcomes,
                                    False if this is for general exploration

        Returns:
            A message indicating success or failure
        """
        if self.role is not ConversationRole.COORDINATOR:
            return "Only Coordinator can set learning intention."

        # Get share ID
        share_id = await KnowledgeTransferManager.get_share_id(self.context)
        if not share_id:
            return "No knowledge package associated with this conversation. Please create a knowledge brief first."

        # Get existing knowledge package
        package = ShareStorage.read_share(share_id)
        if not package:
            return "No knowledge package found. Please create a knowledge brief first."

        # Update the intention
        package.is_intended_to_accomplish_outcomes = is_for_specific_outcomes
        package.updated_at = datetime.utcnow()

        # Save the updated package
        ShareStorage.write_share(share_id, package)

        # Provide appropriate guidance based on the choice
        if is_for_specific_outcomes:
            guidance = "This knowledge package is now set for specific learning outcomes. You'll need to add learning objectives with measurable outcomes."
        else:
            guidance = "This knowledge package is now set for general exploration. No specific learning objectives are required."

        return f"Learning intention updated successfully. {guidance}"
