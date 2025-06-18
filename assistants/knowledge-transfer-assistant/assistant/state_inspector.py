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

        title = brief.title if brief else "Untitled"
        lines.append(f"### {title}")
        lines.append("")

        if brief and brief.description:
            lines.append(brief.description)
            lines.append("")

            # In context transfer mode, show additional context in a dedicated section
            if brief.additional_context:
                lines.append("## Additional Knowledge Context")
                lines.append(brief.additional_context)
                lines.append("")

        # Add learning objectives section if available and progress tracking is enabled
        if share and share.learning_objectives:
            lines.append("## Learning Objectives")
            for objective in share.learning_objectives:
                criteria_complete = sum(1 for c in objective.learning_outcomes if c.achieved)
                criteria_total = len(objective.learning_outcomes)
                lines.append(f"### {objective.name}")
                lines.append(objective.description)
                lines.append(f"**Progress:** {criteria_complete}/{criteria_total} outcomes achieved")

                if objective.learning_outcomes:
                    lines.append("")
                    lines.append("#### Learning Outcomes:")
                    for criterion in objective.learning_outcomes:
                        status_emoji = "✅" if criterion.achieved else "⬜"
                        lines.append(f"- {status_emoji} {criterion.description}")
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

        title = brief.title if brief else "Untitled"
        lines.append(f"### {title}")
        lines.append("")

        if brief and brief.description:
            lines.append(brief.description)
            lines.append("")

            # In context transfer mode, show additional context in a dedicated section
            if brief.additional_context:
                lines.append("## Additional Knowledge Context")
                lines.append(brief.additional_context)
                lines.append("")

        # Add learning objectives section with checkable outcomes if progress tracking is enabled
        if share and share.learning_objectives:
            lines.append("## Learning Objectives")
            for objective in share.learning_objectives:
                criteria_complete = sum(1 for c in objective.learning_outcomes if c.achieved)
                criteria_total = len(objective.learning_outcomes)
                lines.append(f"### {objective.name}")
                lines.append(objective.description)
                lines.append(f"**Progress:** {criteria_complete}/{criteria_total} outcomes achieved")

                if objective.learning_outcomes:
                    lines.append("")
                    lines.append("#### Learning Outcomes:")
                    for criterion in objective.learning_outcomes:
                        status_emoji = "✅" if criterion.achieved else "⬜"
                        completion_info = ""
                        if criterion.achieved and hasattr(criterion, "achieved_at") and criterion.achieved_at:
                            completion_info = f" (achieved on {criterion.achieved_at.strftime('%Y-%m-%d')})"
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
