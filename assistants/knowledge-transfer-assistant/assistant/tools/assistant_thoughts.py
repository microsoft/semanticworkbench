from assistant.domain.thoughts_manager import ThoughtsManager
from assistant.logging import logger

from .base import ToolsBase


class AssistantThoughtsTools(ToolsBase):
    """Tools for managing assistant thoughts."""

    async def forget_thought(self, thought: str) -> str:
        """
        Delete an assistant thought. This should be called when a thought has been resolved, is a duplicate, or is no longer relevant.
        Args:
            thought: The thought to forget. Must be the full text of the thought as it appears in the Assistant Thoughts section.
        Returns:
            Message indicating success or failure
        """  # noqa: E501
        try:
            message = await ThoughtsManager.remove_assistant_thought(
                context=self.context,
                thought=thought,
            )
            if not message:
                message = f"Thought '{thought}' deleted successfully."
            else:
                message = f"Thought '{thought}' deleted, but encountered an issue: {message}"
            logger.info(f"Thought deleted: {thought}")
        except Exception as e:
            logger.exception(f"Failed to delete thought: {e}")
            message = f"Failed to delete thought: {e!s}"
            return message
        return message
