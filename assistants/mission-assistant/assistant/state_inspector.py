"""
Mission assistant inspector state provider.

This module provides the state inspector provider for the mission assistant
to display mission information in the workbench UI's inspector panel.
"""

from typing import Any, List

from semantic_workbench_assistant.assistant_app import (
    AssistantConversationInspectorStateDataModel,
    ConversationContext,
)

from .mission_manager import MissionManager, MissionRole
from .mission_storage import ConversationMissionManager


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

        role = await MissionManager.get_conversation_role(context)
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
        
    async def _format_hq_markdown(self, mission_id: str, role: MissionRole, briefing: Any, status: Any, context: ConversationContext) -> str:
        """Format mission information as markdown for HQ role"""
        mission_name = briefing.mission_name if briefing else "Unnamed Mission"
        mission_status = status.state.value if status else "unknown"
        progress = status.progress_percentage if status else 0
        
        # Build the markdown content
        lines: List[str] = []
        lines.append(f"# Mission: {mission_name}")
        lines.append("")
        lines.append("**Role:** HQ (Definition Stage)")
        lines.append(f"**Status:** {mission_status}")
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
        requests = await MissionManager.get_field_requests(context, include_resolved=False)
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
                lines.append(f"  ID: `{request.artifact_id}`")
                lines.append("")
        else:
            lines.append("## Field Requests")
            lines.append("No open field requests.")
            lines.append("")
        
        # Add active invitation links section
        invitations = await MissionManager.list_active_invitations(context)
        if invitations:
            lines.append("## Active Invitations")
            lines.append("Use these invitation links to add field operatives to this mission:")
            lines.append("")
            
            for invitation in invitations:
                invitation_code = f"{invitation.invitation_id}:{invitation.invitation_token}"
                target_info = f" for {invitation.target_username}" if invitation.target_username else ""
                expiry_date = invitation.expires.strftime("%Y-%m-%d %H:%M UTC")
                
                lines.append(f"- Invitation{target_info}")
                lines.append(f"  **Code:** `{invitation_code}`")
                lines.append(f"  **Expires:** {expiry_date}")
                lines.append(f"  Field operatives can join using: `/join {invitation_code}`")
                lines.append("")
        else:
            lines.append("## Invitations")
            lines.append("No active invitations. Use `/invite [username]` to create an invitation link.")
            lines.append("")
        
        return "\n".join(lines)
        
    async def _format_field_markdown(self, mission_id: str, role: MissionRole, briefing: Any, status: Any, context: ConversationContext) -> str:
        """Format mission information as markdown for Field role"""
        mission_name = briefing.mission_name if briefing else "Unnamed Mission"
        mission_status = status.state.value if status else "unknown"
        progress = status.progress_percentage if status else 0
        
        # Build the markdown content
        lines: List[str] = []
        lines.append(f"# Mission: {mission_name}")
        lines.append("")
        lines.append("**Role:** Field (Working Stage)")
        lines.append(f"**Status:** {mission_status}")
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