"""
Knowledge Transfer assistant inspector state provider.

This module provides the state inspector provider for the knowledge transfer assistant
to display knowledge transfer information in the workbench UI's inspector panel.
"""

import logging
from typing import Any, List

from semantic_workbench_assistant.assistant_app import (
    AssistantConversationInspectorStateDataModel,
    ConversationContext,
)

from .common import detect_assistant_role
from .conversation_share_link import ConversationKnowledgePackageManager
from .data import RequestStatus
from .manager import KnowledgeTransferManager
from .storage import ShareStorage
from .storage_models import ConversationRole

logger = logging.getLogger(__name__)

# Default instructional text to show when no brief has been created
DEFAULT_BRIEF_INSTRUCTION = "_This knowledge brief is displayed in the side panel of all of your team members' conversations, too. Before you share links to your team, ask your assistant to update the brief with whatever details you'd like here. What will help your teammates get off to a good start as they explore the knowledge you are sharing?_"


class ShareInspectorStateProvider:
    """
    Inspector state provider for knowledge transfer information.

    This provider displays knowledge transfer information in the inspector panel
    including transfer state, brief, learning objectives, and information requests based on the
    user's role (Coordinator or Team).

    The content displayed is adapted based on the template configuration:
    - Default: Shows brief, learning objectives, outcomes, and request status
    - Context Transfer: Focuses on knowledge context without objectives or progress tracking
    """

    # Default display name and description
    display_name = "Status"
    description = ""

    def __init__(self, config_provider) -> None:
        self.config_provider = config_provider

    async def is_enabled(self, context: ConversationContext) -> bool:
        return True

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        """
        Get knowledge transfer information for display in the inspector panel.
        """

        # State variables that will determine the content to display.
        conversation_role = await detect_assistant_role(context)

        self.display_name = "Knowledge Overview"
        self.description = "Information about the knowledge space."

        # Determine the conversation's role and knowledge share
        share_id = await ConversationKnowledgePackageManager.get_associated_share_id(context)
        if not share_id:
            return AssistantConversationInspectorStateDataModel(
                data={"content": "No active knowledge package. Start a conversation to create one."}
            )

        # Get knowledge transfer information
        brief = await KnowledgeTransferManager.get_knowledge_brief(context)
        share_info = await KnowledgeTransferManager.get_share_info(context)

        if conversation_role == ConversationRole.COORDINATOR:
            markdown = await self._format_coordinator_markdown(share_id, conversation_role, brief, share_info, context)
        else:
            markdown = await self._format_team_markdown(share_id, conversation_role, brief, share_info, context)

        return AssistantConversationInspectorStateDataModel(data={"content": markdown})

    async def _format_coordinator_markdown(
        self,
        share_id: str,
        role: ConversationRole,
        brief: Any,
        share_info: Any,
        context: ConversationContext,
    ) -> str:
        """Format knowledge transfer information as markdown for Coordinator role"""

        lines: List[str] = []

        # Get the knowledge package
        share = ShareStorage.read_share(share_id)

        lines.append("**Role:** Coordinator")

        # Display knowledge transfer stage
        stage_label = "📋 Organizing Knowledge"
        if share_info:
            stage_label = share_info.get_stage_label(for_coordinator=True)
        lines.append(f"**Stage:** {stage_label}")

        if share_info and share_info.transfer_notes:
            lines.append(f"**Status Message:** {share_info.transfer_notes}")

        lines.append("")

        lines.append("## Knowledge Brief")

        if brief:
            # Show actual brief content when it exists
            title = brief.title
            lines.append(f"### {title}")
            lines.append("")

            if brief.content:
                lines.append(brief.content)
                lines.append("")
        else:
            # Show instructional text when no brief has been created yet
            lines.append("### Knowledge Brief")
            lines.append("")
            lines.append(DEFAULT_BRIEF_INSTRUCTION)
            lines.append("")

        # Add learning objectives section if available and progress tracking is enabled
        if share and share.learning_objectives:
            lines.append("## Learning Objectives")

            # Show overall progress across all team conversations
            achieved_outcomes, total_outcomes = share.get_overall_completion()
            lines.append(
                f"**Overall Progress:** {achieved_outcomes}/{total_outcomes} outcomes achieved by team members"
            )
            lines.append("")

            for objective in share.learning_objectives:
                lines.append(f"### {objective.name}")
                lines.append(objective.description)

                if objective.learning_outcomes:
                    lines.append("")
                    lines.append("#### Learning Outcomes:")
                    for criterion in objective.learning_outcomes:
                        # Check if any team conversation has achieved this outcome
                        achieved_by_any = any(
                            share.is_outcome_achieved_by_conversation(criterion.id, conv_id)
                            for conv_id in share.team_conversations.keys()
                        )
                        status_emoji = "✅" if achieved_by_any else "⬜"

                        # Show which team members achieved this outcome
                        achieved_by_names = []
                        for conv_id, team_conv in share.team_conversations.items():
                            if share.is_outcome_achieved_by_conversation(criterion.id, conv_id):
                                achieved_by_names.append(team_conv.redeemer_name)

                        achievement_info = ""
                        if achieved_by_names:
                            achievement_info = f" (achieved by: {', '.join(achieved_by_names)})"

                        lines.append(f"- {status_emoji} {criterion.description}{achievement_info}")
                lines.append("")

        # Add information requests section
        requests = await KnowledgeTransferManager.get_information_requests(context)
        # Filter out resolved requests
        requests = [req for req in requests if req.status != RequestStatus.RESOLVED]
        if requests:
            lines.append("## Information Requests")
            lines.append(f"**Open requests:** {len(requests)}")
            lines.append("")

            for request in requests[:5]:  # Show only first 5 requests
                priority_emoji = "🔴"
                if hasattr(request.priority, "value"):
                    priority = request.priority.value
                else:
                    priority = request.priority

                if priority == "low":
                    priority_emoji = "🔹"
                elif priority == "medium":
                    priority_emoji = "🔶"
                elif priority == "high":
                    priority_emoji = "🔴"
                elif priority == "critical":
                    priority_emoji = "⚠️"

                lines.append(f"{priority_emoji} **{request.title}** ({request.status})")
                lines.append(request.description)
                lines.append("")
        else:
            lines.append("## Information Requests")
            lines.append("No open information requests.")
            lines.append("")

        # Share URL section
        share_info = await KnowledgeTransferManager.get_share_info(context, share_id)
        share_url = share_info.share_url if share_info else None
        if share_url:
            lines.append("## Share")
            lines.append("")
            # Display the share URL as a properly formatted link
            lines.append("**Share this link with your team members:**")
            lines.append(f"[Knowledge Transfer link]({share_url})")
            lines.append("")
            lines.append("The link never expires and can be used by multiple team members.")
            lines.append("")

        # Add team conversations section
        if share and share.team_conversations:
            lines.append("## Team Conversations")
            lines.append(f"**Active team members:** {len(share.team_conversations)}")
            lines.append("")

            for conv_id, team_conv in share.team_conversations.items():
                achieved, total = share.get_completion_for_conversation(conv_id)
                progress_pct = int((achieved / total * 100)) if total > 0 else 0
                lines.append(f"- **{team_conv.redeemer_name}**: {achieved}/{total} outcomes ({progress_pct}%)")
                lines.append(f"  Joined: {team_conv.joined_at.strftime('%Y-%m-%d %H:%M')}")
                lines.append(f"  Last active: {team_conv.last_active_at.strftime('%Y-%m-%d %H:%M')}")
                lines.append("")

        return "\n".join(lines)

    async def _format_team_markdown(
        self,
        share_id: str,
        role: ConversationRole,
        brief: Any,
        share_info: Any,
        context: ConversationContext,
    ) -> str:
        """Format knowledge transfer information as markdown for Team role"""

        lines: List[str] = []

        # Get the knowledge package
        share = ShareStorage.read_share(share_id)

        lines.append("**Role:** Team")

        # Display knowledge transfer stage for team members
        stage_label = "📚 Learning Mode"
        if share_info:
            stage_label = share_info.get_stage_label(for_coordinator=False)
        lines.append(f"**Stage:** {stage_label}")

        # Add status message if available
        if share_info and share_info.transfer_notes:
            lines.append(f"**Status Message:** {share_info.transfer_notes}")

        lines.append("")

        # Add knowledge description and additional context if available
        lines.append("## Knowledge Brief")

        if brief:
            # Show actual brief content when it exists
            title = brief.title
            lines.append(f"### {title}")
            lines.append("")

            if brief.content:
                lines.append(brief.content)
                lines.append("")
        else:
            # Show message for team members when no brief has been created yet
            lines.append("### Knowledge Brief")
            lines.append("")
            lines.append("_The coordinator is still setting up the knowledge brief. Check back soon!_")
            lines.append("")

        # Add learning objectives section with checkable outcomes if progress tracking is enabled
        if share and share.learning_objectives:
            lines.append("## Learning Objectives")

            # Show my personal progress
            conversation_id = str(context.id)
            achieved_outcomes, total_outcomes = share.get_completion_for_conversation(conversation_id)
            progress_pct = int((achieved_outcomes / total_outcomes * 100)) if total_outcomes > 0 else 0
            lines.append(f"**My Progress:** {achieved_outcomes}/{total_outcomes} outcomes achieved ({progress_pct}%)")
            lines.append("")

            for objective in share.learning_objectives:
                lines.append(f"### {objective.name}")
                lines.append(objective.description)

                if objective.learning_outcomes:
                    lines.append("")
                    lines.append("#### Learning Outcomes:")
                    for criterion in objective.learning_outcomes:
                        # Check if I've achieved this outcome
                        achieved_by_me = share.is_outcome_achieved_by_conversation(criterion.id, conversation_id)
                        status_emoji = "✅" if achieved_by_me else "⬜"

                        completion_info = ""
                        if achieved_by_me:
                            # Find my achievement record
                            my_achievements = share.get_achievements_for_conversation(conversation_id)
                            for achievement in my_achievements:
                                if achievement.outcome_id == criterion.id and achievement.achieved:
                                    completion_info = f" (achieved on {achievement.achieved_at.strftime('%Y-%m-%d')})"
                                    break

                        lines.append(f"- {status_emoji} {criterion.description}{completion_info}")
                lines.append("")

        # Add my information requests section
        requests = await KnowledgeTransferManager.get_information_requests(context)
        my_requests = [r for r in requests if r.conversation_id == str(context.id)]
        if my_requests:
            lines.append("## My Information Requests")
            pending = [r for r in my_requests if r.status != "resolved"]
            resolved = [r for r in my_requests if r.status == "resolved"]

            if pending:
                lines.append("### Pending Requests:")
                for request in pending[:3]:  # Show only first 3 pending requests
                    priority_emoji = "🔶"  # default medium
                    if hasattr(request.priority, "value"):
                        priority = request.priority.value
                    else:
                        priority = request.priority

                    if priority == "low":
                        priority_emoji = "🔹"
                    elif priority == "medium":
                        priority_emoji = "🔶"
                    elif priority == "high":
                        priority_emoji = "🔴"
                    elif priority == "critical":
                        priority_emoji = "⚠️"

                    lines.append(f"{priority_emoji} **{request.title}** ({request.status})")
                    lines.append("")

            if resolved:
                lines.append("### Resolved Requests:")
                for request in resolved[:3]:  # Show only first 3 resolved requests
                    lines.append(f"✅ **{request.title}**")
                    if hasattr(request, "resolution") and request.resolution:
                        lines.append(f"  *Resolution:* {request.resolution}")
                    lines.append("")
        else:
            lines.append("## Information Requests")
            lines.append("You haven't created any information requests yet.")

        return "\n".join(lines)
