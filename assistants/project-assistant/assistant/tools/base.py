"""
Base classes for Knowledge Transfer Assistant tools.
"""

from semantic_workbench_assistant.assistant_app import ConversationContext


class ToolsBase:
    """Base class for tool functionality."""

    def __init__(self, context: ConversationContext):
        """
        Initialize the tools base with the current conversation context.

        Args:
            context: The conversation context
            role: The assistant's role (ConversationRole enum)
        """
        self.context = context
