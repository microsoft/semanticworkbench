"""
Sharing inspector for information requests and responses.
"""

from typing import Any, List

from semantic_workbench_assistant.assistant_app import (
    AssistantConversationInspectorStateDataModel,
    ConversationContext,
)

from ..common import detect_assistant_role
from ..conversation_share_link import ConversationKnowledgePackageManager
from ..data import RequestStatus
from ..manager import KnowledgeTransferManager
from ..storage import ShareStorage
from ..storage_models import ConversationRole
from .common import get_priority_emoji, get_status_emoji


class SharingInspector:
    """
    Inspector for information requests and responses.

    Shows pending and resolved information requests.
    """

    display_name = "🔗 Sharing"
    description = "Sharing and information requests"
    state_id = "requests"

    def __init__(self, config_provider) -> None:
        self.config_provider = config_provider

    async def is_enabled(self, context: ConversationContext) -> bool:
        return True

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        """Get information requests for display."""

        conversation_role = await detect_assistant_role(context)

        # Get share information
        share_id = await ConversationKnowledgePackageManager.get_associated_share_id(context)
        if not share_id:
            return AssistantConversationInspectorStateDataModel(
                data={"content": "No active knowledge package. Start a conversation to create one."}
            )

        requests = await KnowledgeTransferManager.get_information_requests(context)

        if conversation_role == ConversationRole.COORDINATOR:
            markdown = await self._format_coordinator_requests(requests, context)
        else:
            markdown = await self._format_team_requests(requests, context)

        return AssistantConversationInspectorStateDataModel(data={"content": markdown})

    async def _format_coordinator_requests(self, requests: List[Any], context: ConversationContext) -> str:
        """Format sharing information and requests for coordinator."""

        lines: List[str] = []

        # Get share information first
        share_id = await ConversationKnowledgePackageManager.get_associated_share_id(context)

        # Share URL section at the top
        share_info = await KnowledgeTransferManager.get_share_info(context, share_id)
        share_url = share_info.share_url if share_info else None
        if share_url:
            lines.append("## Share Link")
            lines.append("")
            lines.append("**Share this link with your team members:**")
            lines.append(f"[Knowledge Transfer link]({share_url})")
            lines.append("")
            lines.append("The link never expires and can be used by multiple team members.")
            lines.append("")

        # Filter requests by status
        pending_requests = [req for req in requests if req.status != RequestStatus.RESOLVED]
        resolved_requests = [req for req in requests if req.status == RequestStatus.RESOLVED]

        lines.append("## Information Requests")
        lines.append("")

        if pending_requests:
            lines.append(f"### Open Requests ({len(pending_requests)})")
            lines.append("")

            for request in pending_requests:
                priority_emoji = get_priority_emoji(request.priority)
                status_emoji = get_status_emoji(request.status)
                lines.append(f"{priority_emoji} **{request.title}** {status_emoji}")
                lines.append(f"*From:* {request.conversation_id}")
                lines.append(request.description)
                lines.append("")

        if resolved_requests:
            lines.append(f"### Resolved Requests ({len(resolved_requests)})")
            lines.append("")

            for request in resolved_requests[:5]:  # Show only first 5 resolved
                lines.append(f"✅ **{request.title}**")
                lines.append(f"*From:* {request.conversation_id}")
                if hasattr(request, 'resolution') and request.resolution:
                    lines.append(f"*Resolution:* {request.resolution}")
                lines.append("")

        if not pending_requests and not resolved_requests:
            lines.append("No information requests yet.")
            lines.append("")
            lines.append("_Team members can ask questions and create information requests that will appear here._")

        # Team summary
        if share_id:
            share = ShareStorage.read_share(share_id)
        else:
            share = None
        if share and share.team_conversations:
            lines.append("## Team Summary")
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

    async def _format_team_requests(self, requests: List[Any], context: ConversationContext) -> str:
        """Format sharing information and requests for team members."""

        lines: List[str] = []

        # Filter to my requests only
        my_requests = [r for r in requests if r.conversation_id == str(context.id)]

        lines.append("## My Information Requests")

        if my_requests:
            pending = [r for r in my_requests if r.status != "resolved"]
            resolved = [r for r in my_requests if r.status == "resolved"]

            if pending:
                lines.append(f"### Pending Requests ({len(pending)})")
                lines.append("")
                for request in pending:
                    priority_emoji = get_priority_emoji(request.priority)
                    status_emoji = get_status_emoji(request.status)
                    lines.append(f"{priority_emoji} **{request.title}** {status_emoji}")
                    lines.append(request.description)
                    lines.append("")

            if resolved:
                lines.append(f"### Resolved Requests ({len(resolved)})")
                lines.append("")
                for request in resolved:
                    lines.append(f"✅ **{request.title}**")
                    if hasattr(request, "resolution") and request.resolution:
                        lines.append(f"*Resolution:* {request.resolution}")
                    lines.append("")
        else:
            lines.append("You haven't created any information requests yet.")
            lines.append("")
            lines.append("_Your assistant will help you create information requests to the knowledge coordinator if it is unable to answer your questions directly._")

        return "\n".join(lines)