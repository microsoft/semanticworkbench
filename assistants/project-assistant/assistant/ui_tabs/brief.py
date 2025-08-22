"""
Brief inspector for knowledge transfer status and brief information.
"""

from semantic_workbench_assistant.assistant_app import (
    AssistantConversationInspectorStateDataModel,
    ConversationContext,
)

from assistant.data import ConversationRole, Share
from assistant.domain.share_manager import ShareManager

from .common import get_stage_label

# Default instructional text to show when no brief has been created
DEFAULT_BRIEF_INSTRUCTION = "_This knowledge brief is displayed in the side panel of all of your team members' conversations, too. Before you share links to your team, ask your assistant to update the brief with whatever details you'd like here. What will help your teammates get off to a good start as they explore the knowledge you are sharing?_"  # noqa: E501


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

        share = await ShareManager.get_share(context)

        conversation_role = await ShareManager.get_conversation_role(context)
        if conversation_role == ConversationRole.COORDINATOR:
            markdown = await self._format_coordinator_brief(share)
        else:
            markdown = await self._format_team_brief(share)

        return AssistantConversationInspectorStateDataModel(data={"content": markdown})

    async def _format_coordinator_brief(
        self,
        share: Share,
    ) -> str:
        """Format brief information for coordinator."""

        lines: list[str] = []

        # Stage
        stage_label = get_stage_label(share, for_coordinator=True)
        lines.append(f"**Stage:** {stage_label}")

        # Audience and takeaways
        lines.append("## Audience")
        lines.append(share.audience if share.audience else "_No audience defined._")

        if share.audience_takeaways:
            lines.append("### Key Takeaways")
            lines.append("")
            for takeaway in share.audience_takeaways:
                lines.append(f"- {takeaway}")
            lines.append("")

        brief = share.brief
        if brief and brief.title:
            title = brief.title
            lines.append(f"## {title}")
            lines.append("")
        else:
            lines.append("## Knowledge Brief")
            lines.append("")

        if brief and brief.content:
            lines.append(brief.content)
            lines.append("")
        else:
            lines.append(DEFAULT_BRIEF_INSTRUCTION)
            lines.append("")

        return "\n".join(lines)

    async def _format_team_brief(self, share: Share) -> str:
        """Format brief information for team members."""

        lines: list[str] = []

        # Stage
        stage_label = get_stage_label(share, for_coordinator=False)
        lines.append(f"**Stage:** {stage_label}")

        brief = share.brief
        if brief:
            title = brief.title
            lines.append(f"## {title}")
            lines.append("")

        if share.audience_takeaways:
            lines.append("### Key Takeaways")
            lines.append("")
            for takeaway in share.audience_takeaways:
                lines.append(f"- {takeaway}")
            lines.append("")

        if brief and brief.content:
            lines.append(brief.content)
            lines.append("")
        else:
            lines.append("## Knowledge Brief")
            lines.append("")
            lines.append("_The coordinator is still setting up the knowledge brief. Check back soon!_")
            lines.append("")

        return "\n".join(lines)
