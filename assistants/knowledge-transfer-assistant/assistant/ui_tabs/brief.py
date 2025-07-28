"""
Brief inspector for knowledge transfer status and brief information.
"""

from typing import Any, List

from semantic_workbench_assistant.assistant_app import (
    AssistantConversationInspectorStateDataModel,
    ConversationContext,
)

from assistant.common import detect_assistant_role
from assistant.domain.share_manager import ShareManager
from assistant.domain import KnowledgeTransferManager
from assistant.data import ConversationRole
from .common import get_stage_label


# Default instructional text to show when no brief has been created
DEFAULT_BRIEF_INSTRUCTION = "_This knowledge brief is displayed in the side panel of all of your team members' conversations, too. Before you share links to your team, ask your assistant to update the brief with whatever details you'd like here. What will help your teammates get off to a good start as they explore the knowledge you are sharing?_"


class BriefInspector:
    """
    Inspector for knowledge transfer status and brief information.

    Shows role, stage, status message, and knowledge brief content.
    """

    display_name = "📋 Brief"
    description = "Knowledge share overview"
    state_id = "brief"

    def __init__(self, config_provider) -> None:
        self.config_provider = config_provider

    async def is_enabled(self, context: ConversationContext) -> bool:
        return True

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        """Get brief and status information for display."""

        conversation_role = await detect_assistant_role(context)

        # Get share information
        share_id = await ShareManager.get_associated_share_id(context)
        if not share_id:
            return AssistantConversationInspectorStateDataModel(
                data={"content": "No active knowledge package. Start a conversation to create one."}
            )

        brief = await KnowledgeTransferManager.get_knowledge_brief(context)
        share_info = await KnowledgeTransferManager.get_share(context)

        if conversation_role == ConversationRole.COORDINATOR:
            markdown = await self._format_coordinator_brief(share_id, brief, share_info, context)
        else:
            markdown = await self._format_team_brief(share_id, brief, share_info, context)

        return AssistantConversationInspectorStateDataModel(data={"content": markdown})

    async def _format_coordinator_brief(
        self, share_id: str, brief: Any, share_info: Any, context: ConversationContext
    ) -> str:
        """Format brief information for coordinator."""

        lines: List[str] = []

        lines.append("**Role:** Coordinator")

        # Display knowledge transfer stage
        stage_label = "📋 Organizing Knowledge"
        if share_info:
            stage_label = get_stage_label(share_info, for_coordinator=True)
        lines.append(f"**Stage:** {stage_label}")

        if share_info and share_info.transfer_notes:
            lines.append(f"**Status Message:** {share_info.transfer_notes}")

        lines.append("")

        # Knowledge Brief section

        if brief:
            title = brief.title
            lines.append(f"## {title}")
            lines.append("")

            if brief.content:
                lines.append(brief.content)
                lines.append("")
        else:
            lines.append("## Knowledge Brief")
            lines.append("")
            lines.append(DEFAULT_BRIEF_INSTRUCTION)
            lines.append("")

        return "\n".join(lines)

    async def _format_team_brief(self, share_id: str, brief: Any, share_info: Any, context: ConversationContext) -> str:
        """Format brief information for team members."""

        lines: List[str] = []

        lines.append("**Role:** Team")

        # Display knowledge transfer stage for team members
        stage_label = "📚 Learning Mode"
        if share_info:
            stage_label = get_stage_label(share_info, for_coordinator=False)
        lines.append(f"**Stage:** {stage_label}")

        # Add status message if available
        if share_info and share_info.transfer_notes:
            lines.append(f"**Status Message:** {share_info.transfer_notes}")

        lines.append("")

        # Knowledge Brief section
        if brief:
            title = brief.title
            lines.append(f"## {title}")
            lines.append("")

            if brief.content:
                lines.append(brief.content)
                lines.append("")
        else:
            lines.append("## Knowledge Brief")
            lines.append("")
            lines.append("_The coordinator is still setting up the knowledge brief. Check back soon!_")
            lines.append("")

        return "\n".join(lines)
