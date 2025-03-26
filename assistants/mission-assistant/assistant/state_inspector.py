"""
Mission assistant inspector state provider.

This module provides the state inspector provider for the mission assistant
to display mission information in the workbench UI's inspector panel.
"""

from typing import Any, Dict

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
        
        # Base information for both roles
        mission_info: Dict[str, Any] = {
            "mission_id": mission_id,
            "role": role.value if role else "unknown",
            "mission_name": briefing.mission_name if briefing else "Unnamed Mission",
            "mission_status": status.state.value if status else "unknown",
            "progress": status.progress_percentage if status else 0,
        }

        # Add role-specific information
        if role == MissionRole.HQ:
            # Add HQ-specific info (pending invitations, field requests)
            requests = await MissionManager.get_field_requests(context, include_resolved=False)
            
            mission_info.update({
                "open_requests_count": len(requests),
                "open_requests": [
                    {
                        "id": request.artifact_id,
                        "title": request.title,
                        "priority": request.priority.value if hasattr(request.priority, "value") else request.priority,
                        "status": request.status,
                    }
                    for request in requests[:5]  # Show only first 5 requests
                ]
            })
            
            # If there's a briefing, add goals information
            if briefing and briefing.goals:
                mission_info["goals"] = [
                    {
                        "name": goal.name,
                        "description": goal.description,
                        "criteria_complete": sum(1 for c in goal.success_criteria if c.completed),
                        "criteria_total": len(goal.success_criteria),
                    }
                    for goal in briefing.goals
                ]
        else:
            # Field role - show field requests created by this conversation
            requests = await MissionManager.get_field_requests(context)
            my_requests = [r for r in requests if r.conversation_id == str(context.id)]
            
            mission_info.update({
                "my_requests_count": len(my_requests),
                "my_requests": [
                    {
                        "id": request.artifact_id,
                        "title": request.title,
                        "status": request.status,
                        "priority": request.priority.value if hasattr(request.priority, "value") else request.priority,
                        "resolved": request.status == "resolved",
                    }
                    for request in my_requests[:5]  # Show only first 5 requests
                ]
            })
            
            # If there's a briefing, add goals and criteria to track progress
            if briefing and briefing.goals:
                mission_info["goals"] = []
                for goal in briefing.goals:
                    criteria = []
                    for criterion in goal.success_criteria:
                        criteria.append({
                            "description": criterion.description,
                            "completed": criterion.completed,
                            "completed_at": criterion.completed_at.isoformat() if criterion.completed_at else None,
                        })
                    
                    mission_info["goals"].append({
                        "name": goal.name,
                        "description": goal.description,
                        "criteria": criteria,
                    })

        return AssistantConversationInspectorStateDataModel(data=mission_info)