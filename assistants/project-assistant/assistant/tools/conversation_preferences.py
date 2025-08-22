"""
Project setup tools for Knowledge Transfer Assistant.

Tools for configuring knowledge shares.
"""

from assistant.domain.conversation_preferences_manager import ConversationPreferencesManager

from .base import ToolsBase


class ConversationPreferencesTools(ToolsBase):
    async def update_preferred_communication_style(self, style: str) -> str:
        """
        Update the preferred communication style for the conversation.

        Args:
            style: The preferred communication style to set. This should include all of the users instructions about how the assistant should communicate with the user. It is not just a single style, but a comprehensive set of instructions.

        Returns:
            A message indicating success or failure
        """  # noqa: E501
        try:
            await ConversationPreferencesManager.update_preferred_communication_style(
                context=self.context,
                preferred_communication_style=style,
            )
            return "Preferred conversation style updated successfully"
        except Exception as e:
            return f"Failed to update preferred conversation style: {e!s}"
