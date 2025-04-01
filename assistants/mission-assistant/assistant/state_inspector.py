"""
Mission assistant inspector state provider.

This module provides the state inspector provider for the mission assistant
to display mission information in the workbench UI's inspector panel.
"""

import logging
from typing import Any, List

from semantic_workbench_assistant.assistant_app import (
    AssistantConversationInspectorStateDataModel,
    ConversationContext,
)

from .mission_data import RequestStatus
from .mission_manager import MissionManager
from .mission_storage import ConversationMissionManager, MissionRole

logger = logging.getLogger(__name__)


class MissionInspectorStateProvider:
    """
    Inspector state provider for mission information.

    This provider displays mission-specific information in the inspector panel
    including mission state, briefing, goals, and field requests based on the
    user's role (HQ or Field).
    """

    display_name = "Mission Status"
    description = "Current mission information including briefing, goals, and request status."

    def __init__(self, config_provider) -> None:
        self.config_provider = config_provider

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        """
        Get mission information for display in the inspector panel.

        Returns different information based on the conversation's role (HQ or Field).
        """
        # Determine the conversation's role and mission
        mission_id = await ConversationMissionManager.get_conversation_mission(context)
        if not mission_id:
            return AssistantConversationInspectorStateDataModel(
                data={"content": "No active mission. Start a conversation to create one."}
            )

        role = await ConversationMissionManager.get_conversation_role(context)
        if not role:
            return AssistantConversationInspectorStateDataModel(
                data={"content": "Role not assigned. Please restart the conversation."}
            )

        # Get mission information
        briefing = await MissionManager.get_mission_briefing(context)
        status = await MissionManager.get_mission_status(context)

        # Generate nicely formatted markdown for the state panel
        if role == MissionRole.HQ:
            # Format for HQ role
            markdown = await self._format_hq_markdown(mission_id, role, briefing, status, context)
        else:
            # Format for Field role
            markdown = await self._format_field_markdown(mission_id, role, briefing, status, context)

        return AssistantConversationInspectorStateDataModel(data={"content": markdown})

    async def _format_hq_markdown(
        self, mission_id: str, role: MissionRole, briefing: Any, status: Any, context: ConversationContext
    ) -> str:
        """Format mission information as markdown for HQ role"""
        mission_name = briefing.mission_name if briefing else "Unnamed Mission"
        progress = status.progress_percentage if status else 0

        # Build the markdown content
        lines: List[str] = []
        lines.append(f"# Mission: {mission_name}")
        lines.append("")

        # Determine stage based on mission status
        stage_label = "Definition Stage"
        if status and status.state:
            if status.state.value == "planning":
                stage_label = "Definition Stage"
            elif status.state.value == "ready_for_field":
                stage_label = "Ready for Field"
            elif status.state.value == "in_progress":
                stage_label = "Working Stage"
            elif status.state.value == "completed":
                stage_label = "Completed Stage"
            elif status.state.value == "aborted":
                stage_label = "Aborted Stage"

        lines.append("**Role:** HQ")
        lines.append(f"**Status:** {stage_label}")
        lines.append(f"**Progress:** {progress}%")
        lines.append("")

        # Add mission description if available
        if briefing and briefing.mission_description:
            lines.append("## Description")
            lines.append(briefing.mission_description)
            lines.append("")

        # Add goals section if available
        if briefing and briefing.goals:
            lines.append("## Goals")
            for goal in briefing.goals:
                criteria_complete = sum(1 for c in goal.success_criteria if c.completed)
                criteria_total = len(goal.success_criteria)
                lines.append(f"### {goal.name}")
                lines.append(goal.description)
                lines.append(f"**Progress:** {criteria_complete}/{criteria_total} criteria complete")

                if goal.success_criteria:
                    lines.append("")
                    lines.append("#### Success Criteria:")
                    for criterion in goal.success_criteria:
                        status_emoji = "✅" if criterion.completed else "⬜"
                        lines.append(f"- {status_emoji} {criterion.description}")
                lines.append("")

        # Add field requests section
        requests = await MissionManager.get_field_requests(context)
        # Filter out resolved requests
        requests = [req for req in requests if req.status != RequestStatus.RESOLVED]
        if requests:
            lines.append("## Field Requests")
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
                lines.append(f"  **Request ID for resolution:** `{request.request_id}`")
                lines.append("")
        else:
            lines.append("## Field Requests")
            lines.append("No open field requests.")
            lines.append("")

        # Display invitation information
        lines.append("## Mission Invitation")
        
        # Try to get the latest invitation
        from .mission import MissionInvitation
        latest_invitation = None
        invitations_path = MissionInvitation._get_invitations_path(context)
        
        if invitations_path.exists():
            try:
                # Use the proper storage method from the library
                from semantic_workbench_assistant.storage import read_model
                invitations = read_model(invitations_path, MissionInvitation.InvitationsCollection)
                if invitations:
                    # Convert dictionary invitations to proper Invitation objects
                    from .mission import MissionInvitation
                    proper_invitations = []
                    
                    for inv in invitations.invitations:
                        # If it's a dict, convert to proper Invitation object
                        if isinstance(inv, dict):
                            # Create a proper Invitation instance
                            proper_inv = MissionInvitation.Invitation(**inv)
                            proper_invitations.append(proper_inv)
                        else:
                            # Already an Invitation object
                            proper_invitations.append(inv)
                    
                    # Now filter for non-redeemed invitations
                    active_invitations = [inv for inv in proper_invitations if not inv.redeemed]
                else:
                    active_invitations = []
                    
                if active_invitations:
                    # Sort by creation time (newest first)
                    sorted_invitations = sorted(active_invitations, key=lambda x: x.created_at, reverse=True)
                    latest_invitation = sorted_invitations[0]
            except Exception as e:
                logger.warning(f"Failed to read invitation data: {e}")
                
        if latest_invitation:
            # Format the code
            invitation_code = f"{latest_invitation.invitation_id}:{latest_invitation.token}"
            
            # Show invitation details
            if latest_invitation.target_username:
                lines.append(f"Active invitation for: **{latest_invitation.target_username}**")
            else:
                lines.append("Active invitation (anyone can use):")
            
            lines.append(f"**Invitation Code:** `{invitation_code}`")
            lines.append(f"**Created:** {latest_invitation.created_at.strftime('%Y-%m-%d %H:%M')}")
            lines.append(f"**Expires:** {latest_invitation.expires_at.strftime('%Y-%m-%d %H:%M')}")
        else:
            lines.append("No active invitations. Use `/invite` to generate a mission invitation code.")
            
        lines.append("")
        lines.append("Field personnel can join using the `/join <code>` command with the invitation code.")

        lines.append("")

        return "\n".join(lines)

    async def _format_field_markdown(
        self, mission_id: str, role: MissionRole, briefing: Any, status: Any, context: ConversationContext
    ) -> str:
        """Format mission information as markdown for Field role"""
        mission_name = briefing.mission_name if briefing else "Unnamed Mission"
        progress = status.progress_percentage if status else 0

        # Build the markdown content
        lines: List[str] = []
        lines.append(f"# Mission: {mission_name}")
        lines.append("")

        # Determine stage based on mission status
        stage_label = "Working Stage"
        if status and status.state:
            if status.state.value == "planning":
                stage_label = "Definition Stage"
            elif status.state.value == "ready_for_field":
                stage_label = "Working Stage"
            elif status.state.value == "in_progress":
                stage_label = "Working Stage"
            elif status.state.value == "completed":
                stage_label = "Completed Stage"
            elif status.state.value == "aborted":
                stage_label = "Aborted Stage"

        lines.append(f"**Role:** Field ({stage_label})")
        lines.append(f"**Status:** {stage_label}")
        lines.append(f"**Progress:** {progress}%")
        lines.append("")

        # Add mission description if available
        if briefing and briefing.mission_description:
            lines.append("## Mission Brief")
            lines.append(briefing.mission_description)
            lines.append("")

        # Add goals section with checkable criteria
        if briefing and briefing.goals:
            lines.append("## Objectives")
            for goal in briefing.goals:
                criteria_complete = sum(1 for c in goal.success_criteria if c.completed)
                criteria_total = len(goal.success_criteria)
                lines.append(f"### {goal.name}")
                lines.append(goal.description)
                lines.append(f"**Progress:** {criteria_complete}/{criteria_total} criteria complete")

                if goal.success_criteria:
                    lines.append("")
                    lines.append("#### Success Criteria:")
                    for criterion in goal.success_criteria:
                        status_emoji = "✅" if criterion.completed else "⬜"
                        completion_info = ""
                        if criterion.completed and hasattr(criterion, "completed_at") and criterion.completed_at:
                            completion_info = f" (completed on {criterion.completed_at.strftime('%Y-%m-%d')})"
                        lines.append(f"- {status_emoji} {criterion.description}{completion_info}")
                lines.append("")

        # Add my field requests section
        requests = await MissionManager.get_field_requests(context)
        my_requests = [r for r in requests if r.conversation_id == str(context.id)]

        if my_requests:
            lines.append("## My Field Requests")
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
            lines.append("## Field Requests")
            lines.append("You haven't created any field requests yet.")

        return "\n".join(lines)
