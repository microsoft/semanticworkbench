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
from .data import RequestPriority, RequestStatus
from .manager import KnowledgeTransferManager
from .storage import ShareStorage
from .storage_models import ConversationRole

logger = logging.getLogger(__name__)

# Default instructional text to show when no brief has been created
DEFAULT_BRIEF_INSTRUCTION = "_This knowledge brief is displayed in the side panel of all of your team members' conversations, too. Before you share links to your team, ask your assistant to update the brief with whatever details you'd like here. What will help your teammates get off to a good start as they explore the knowledge you are sharing?_"


def get_status_emoji(status: RequestStatus) -> str:
    """Get emoji representation for request status."""
    status_emojis = {
        RequestStatus.NEW: "🆕",  # New
        RequestStatus.ACKNOWLEDGED: "👀",  # Acknowledged/Seen
        RequestStatus.IN_PROGRESS: "⚡",  # In Progress
        RequestStatus.RESOLVED: "✅",  # Resolved/Complete
        RequestStatus.DEFERRED: "⏸️",  # Deferred/Paused
    }
    return status_emojis.get(status, "❓")  # Unknown status fallback


def get_priority_emoji(priority: RequestPriority) -> str:
    """Get emoji representation for request priority."""
    priority_emojis = {
        RequestPriority.LOW: "🔹",  # Low priority - blue diamond
        RequestPriority.MEDIUM: "🔶",  # Medium priority - orange diamond
        RequestPriority.HIGH: "🔴",  # High priority - red circle
        RequestPriority.CRITICAL: "⚠️",  # Critical priority - warning sign
    }
    return priority_emojis.get(priority, "🔹")  # Default to low priority emoji


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
        share_id = await ConversationKnowledgePackageManager.get_associated_share_id(context)
        if not share_id:
            return AssistantConversationInspectorStateDataModel(
                data={"content": "No active knowledge package. Start a conversation to create one."}
            )

        brief = await KnowledgeTransferManager.get_knowledge_brief(context)
        share_info = await KnowledgeTransferManager.get_share_info(context)

        if conversation_role == ConversationRole.COORDINATOR:
            markdown = await self._format_coordinator_brief(share_id, brief, share_info, context)
        else:
            markdown = await self._format_team_brief(share_id, brief, share_info, context)

        return AssistantConversationInspectorStateDataModel(data={"content": markdown})

    async def _format_coordinator_brief(self, share_id: str, brief: Any, share_info: Any, context: ConversationContext) -> str:
        """Format brief information for coordinator."""

        lines: List[str] = []

        lines.append("**Role:** Coordinator")

        # Display knowledge transfer stage
        stage_label = "📋 Organizing Knowledge"
        if share_info:
            stage_label = share_info.get_stage_label(for_coordinator=True)
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
            stage_label = share_info.get_stage_label(for_coordinator=False)
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


class LearningInspector:
    """
    Inspector for learning objectives and progress tracking.

    Shows learning objectives, outcomes, and completion progress.
    """

    display_name = "🎯 Learning"
    description = "Learning objectives and progress tracking"
    state_id = "objectives"

    def __init__(self, config_provider) -> None:
        self.config_provider = config_provider

    async def is_enabled(self, context: ConversationContext) -> bool:
        return True

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        """Get learning objectives and progress information."""

        conversation_role = await detect_assistant_role(context)

        # Get share information
        share_id = await ConversationKnowledgePackageManager.get_associated_share_id(context)
        if not share_id:
            return AssistantConversationInspectorStateDataModel(
                data={"content": "No active knowledge package. Start a conversation to create one."}
            )

        share = ShareStorage.read_share(share_id)

        if conversation_role == ConversationRole.COORDINATOR:
            markdown = await self._format_coordinator_objectives(share, context)
        else:
            markdown = await self._format_team_objectives(share, context)

        return AssistantConversationInspectorStateDataModel(data={"content": markdown})

    async def _format_coordinator_objectives(self, share: Any, context: ConversationContext) -> str:
        """Format learning objectives for coordinator."""

        lines: List[str] = []

        if not share or not share.learning_objectives:
            lines.append("## Learning Objectives")
            lines.append("")
            lines.append("_No learning objectives have been set up yet. When shared, the assistant will help your recipients explore the knowledge in a more open way, helping them discover the important aspects of the knowledge without specific objectives or outcomes. If you would like to have a more formal process, ask your assistant to help you create learning objectives and outcomes._")
            lines.append("")
            return "\n".join(lines)

        lines.append("## Team Progress")
        lines.append("")

        # Overall progress summary
        total_outcomes = sum(len(obj.learning_outcomes) for obj in share.learning_objectives if obj.learning_outcomes)
        if total_outcomes > 0 and share.team_conversations:
            for conv_id, team_conv in share.team_conversations.items():
                achieved, total = share.get_completion_for_conversation(conv_id)
                progress_pct = int((achieved / total * 100)) if total > 0 else 0
                lines.append(f"- **{team_conv.redeemer_name}**: {achieved}/{total} outcomes ({progress_pct}%)")
            lines.append("")

        # Detailed objectives
        lines.append("## Learning Objectives")
        for objective in share.learning_objectives:
            lines.append(f"### 🎯 {objective.name}")
            lines.append(objective.description)

            if objective.learning_outcomes:
                lines.append("")
                lines.append("#### Learning Outcomes")
                for criterion in objective.learning_outcomes:
                    # Check if any team conversation has achieved this outcome
                    achieved_by_any = any(
                        share.is_outcome_achieved_by_conversation(criterion.id, conv_id)
                        for conv_id in share.team_conversations.keys()
                    )
                    status_emoji = "✅" if achieved_by_any else "⬜"

                    # Show progress ratio for team completion
                    achieved_count = 0
                    total_team_count = len(share.team_conversations)

                    for conv_id in share.team_conversations.keys():
                        if share.is_outcome_achieved_by_conversation(criterion.id, conv_id):
                            achieved_count += 1

                    achievement_info = ""
                    if total_team_count > 0:
                        achievement_info = f" ({achieved_count}/{total_team_count})"

                    lines.append(f"- {status_emoji} {criterion.description}{achievement_info}")
            lines.append("")

        return "\n".join(lines)

    async def _format_team_objectives(self, share: Any, context: ConversationContext) -> str:
        """Format learning objectives for team members."""

        lines: List[str] = []

        if not share or not share.learning_objectives:
            lines.append("## Learning Objectives")
            lines.append("")
            lines.append("_The coordinator hasn't set up specific learning objectives for this shared knowledge. Enjoy exploring at your own pace! The assistant will guide you towards important information as you go._")
            lines.append("")
            return "\n".join(lines)

        lines.append("## Learning Objectives")
        lines.append("")

        # Show my personal progress
        conversation_id = str(context.id)
        achieved_outcomes, total_outcomes = share.get_completion_for_conversation(conversation_id)
        progress_pct = int((achieved_outcomes / total_outcomes * 100)) if total_outcomes > 0 else 0
        lines.append(f"**My Progress:** {achieved_outcomes}/{total_outcomes} outcomes achieved ({progress_pct}%)")
        lines.append("")

        for objective in share.learning_objectives:
            lines.append(f"### 🎯 {objective.name}")
            lines.append(objective.description)

            if objective.learning_outcomes:
                lines.append("")
                lines.append("#### Learning Outcomes")
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

        return "\n".join(lines)


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

        # Get share information first
        share_id = await ConversationKnowledgePackageManager.get_associated_share_id(context)

        # Show team information for context
        if share_id:
            share = ShareStorage.read_share(share_id)
        else:
            share = None

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


class DebugInspector:
    """
    Inspector for debug information and internal assistant state.
    
    Shows the knowledge digest and other internal information maintained by the assistant.
    """
    
    display_name = "🐛 Debug"
    description = "Internal assistant state and knowledge digest"
    state_id = "debug"
    
    def __init__(self, config_provider) -> None:
        self.config_provider = config_provider
    
    async def is_enabled(self, context: ConversationContext) -> bool:
        return True
    
    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        """Get debug information for display."""
        
        # Get share information
        share_id = await ConversationKnowledgePackageManager.get_associated_share_id(context)
        if not share_id:
            return AssistantConversationInspectorStateDataModel(
                data={"content": "No active knowledge package. Start a conversation to create one."}
            )
        
        markdown = await self._format_debug_info(share_id, context)
        return AssistantConversationInspectorStateDataModel(data={"content": markdown})
    
    async def _format_debug_info(self, share_id: str, context: ConversationContext) -> str:
        """Format debug information including knowledge digest."""
        
        lines: List[str] = []
        
        lines.append("## Debug Information")
        lines.append("")
        lines.append("This panel shows internal information maintained by the assistant. This data is automatically")
        lines.append("generated and updated by the assistant and is not directly editable by users.")
        lines.append("")
        
        # Get the knowledge digest
        try:
            digest = await KnowledgeTransferManager.get_knowledge_digest(context)
            
            lines.append("## Knowledge Digest")
            lines.append("")
            lines.append("The knowledge digest is an internal summary of the conversation that the assistant")
            lines.append("maintains to help understand the context and key information being shared. It is")
            lines.append("automatically updated as the conversation progresses.")
            lines.append("")
            
            if digest and digest.content:
                lines.append("### Current Digest Content")
                lines.append("")
                lines.append("```markdown")
                lines.append(digest.content)
                lines.append("```")
                lines.append("")
            else:
                lines.append("_No knowledge digest has been generated yet. The assistant will create and update_")
                lines.append("_this automatically as the conversation develops._")
                lines.append("")
                
        except Exception as e:
            lines.append("## Knowledge Digest")
            lines.append("")
            lines.append(f"**Error retrieving knowledge digest:** {str(e)}")
            lines.append("")
        
        # Add share metadata for debugging
        try:
            share = ShareStorage.read_share(share_id)
            if share:
                lines.append("## Share Metadata")
                lines.append("")
                lines.append(f"**Share ID:** `{share_id}`")
                lines.append(f"**Created:** {share.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                lines.append(f"**Last Updated:** {share.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
                lines.append(f"**Team Conversations:** {len(share.team_conversations) if share.team_conversations else 0}")
                lines.append(f"**Learning Objectives:** {len(share.learning_objectives) if share.learning_objectives else 0}")
                lines.append(f"**Knowledge Organized:** {share.knowledge_organized}")
                lines.append(f"**Ready for Transfer:** {share.is_ready_for_transfer()}")
                lines.append(f"**Actively Sharing:** {share.is_actively_sharing()}")
                lines.append("")
                
                # Add coordinator conversation info if available
                if share.coordinator_conversation_id:
                    lines.append("### Coordinator Conversation")
                    lines.append(f"**Conversation ID:** `{share.coordinator_conversation_id}`")
                    lines.append("")
                    
        except Exception as e:
            lines.append("## Share Metadata")
            lines.append("")
            lines.append(f"**Error retrieving share metadata:** {str(e)}")
            lines.append("")
        
        return "\n".join(lines)


# Legacy ShareInspectorStateProvider removed - replaced by tabbed inspectors:
# - BriefInspector: Status and knowledge brief
# - LearningInspector: Learning objectives and progress
# - SharingInspector: Information requests and sharing
# - DebugInspector: Internal assistant state and knowledge digest
