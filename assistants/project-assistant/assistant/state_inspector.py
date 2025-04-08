"""
Project assistant inspector state provider.

This module provides the state inspector provider for the project assistant
to display project information in the workbench UI's inspector panel.
"""

import logging
from typing import Any, List

from semantic_workbench_assistant.assistant_app import (
    AssistantConversationInspectorStateDataModel,
    ConversationContext,
)

from .project_data import RequestStatus
from .project_manager import ProjectManager
from .project_storage import ConversationProjectManager, ProjectRole

logger = logging.getLogger(__name__)


class ProjectInspectorStateProvider:
    """
    Inspector state provider for project information.

    This provider displays project-specific information in the inspector panel
    including project state, brief, goals, and information requests based on the
    user's role (Coordinator or Team).
    
    The content displayed is adapted based on the template configuration:
    - Default: Shows brief, goals, criteria, and request status
    - Context Transfer: Focuses on knowledge context without goals or progress tracking
    """

    display_name = "Project Status"
    # Default description - will be updated based on template
    description = "Current project information including brief, goals, and request status."

    def __init__(self, config_provider) -> None:
        self.config_provider = config_provider
        self.is_context_transfer = False

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        """
        Get project information for display in the inspector panel.

        Returns different information based on the conversation's role (Coordinator or Team).
        """
        # First check conversation metadata for setup status
        conversation = await context.get_conversation()
        metadata = conversation.metadata or {}

        # Check if metadata has setup info
        setup_complete = metadata.get("setup_complete", False)
        assistant_mode = metadata.get("assistant_mode", "setup")

        track_progress = True
        if self.config_provider:
            config = await self.config_provider.get(context.assistant)
            track_progress = config.track_progress
            
            # Update description and display name based on template
            self.is_context_transfer = not track_progress
            if self.is_context_transfer:
                self.description = "Context transfer information including knowledge resources and shared content."
                self.display_name = "Knowledge Context"
            else:
                self.description = "Current project information including brief, goals, and request status."
                self.display_name = "Project Status"

        # Double-check with project storage/manager state
        if not setup_complete:
            # Check if we have a project role in storage
            role = await ConversationProjectManager.get_conversation_role(context)
            if role:
                # If we have a role in storage, consider setup complete
                setup_complete = True
                assistant_mode = role.value

                # Update local metadata too
                metadata["setup_complete"] = True
                metadata["assistant_mode"] = role.value
                metadata["project_role"] = role.value

                # Send conversation state event to save the metadata - using None for state values
                try:
                    from semantic_workbench_api_model.workbench_model import AssistantStateEvent

                    await context.send_conversation_state_event(
                        AssistantStateEvent(state_id="setup_complete", event="updated", state=None)
                    )
                    await context.send_conversation_state_event(
                        AssistantStateEvent(state_id="assistant_mode", event="updated", state=None)
                    )
                    await context.send_conversation_state_event(
                        AssistantStateEvent(state_id="project_role", event="updated", state=None)
                    )
                    logger.info(f"Updated metadata based on project role detection: {role.value}")
                except Exception as e:
                    logger.exception(f"Failed to update metadata: {e}")

        # If setup isn't complete, show setup instructions
        if not setup_complete and assistant_mode == "setup":
            setup_markdown = """# Project Assistant Setup

**Role Selection Required**

Before you can access project features, please specify your role:

- Use `/start` to create a new project as Coordinator
- Use `/join <project_id>` to join an existing project as Team member

Type `/help` for more information on available commands.

⚠️ **Note:** Setup is required before you can access any project features.
"""
            return AssistantConversationInspectorStateDataModel(data={"content": setup_markdown})

        # Continue with normal inspector display for already set up conversations
        # Determine the conversation's role and project
        project_id = await ConversationProjectManager.get_conversation_project(context)
        if not project_id:
            return AssistantConversationInspectorStateDataModel(
                data={"content": "No active project. Start a conversation to create one."}
            )

        role = await ConversationProjectManager.get_conversation_role(context)
        if not role:
            return AssistantConversationInspectorStateDataModel(
                data={"content": "Role not assigned. Please restart the conversation."}
            )

        # Get project information
        brief = await ProjectManager.get_project_brief(context)
        dashboard = await ProjectManager.get_project_dashboard(context)

        # Generate nicely formatted markdown for the state panel
        if role == ProjectRole.COORDINATOR:
            # Format for Coordinator role
            markdown = await self._format_coordinator_markdown(
                project_id, role, brief, dashboard, context, track_progress
            )
        else:
            # Format for Team role
            markdown = await self._format_team_markdown(project_id, role, brief, dashboard, context, track_progress)

        return AssistantConversationInspectorStateDataModel(data={"content": markdown})

    async def _format_coordinator_markdown(
        self,
        project_id: str,
        role: ProjectRole,
        brief: Any,
        dashboard: Any,
        context: ConversationContext,
        track_progress: bool,
    ) -> str:
        """Format project information as markdown for Coordinator role"""
        project_name = brief.project_name if brief else "Unnamed Project"
        progress = dashboard.progress_percentage if dashboard and track_progress else 0

        # Build the markdown content
        lines: List[str] = []
        lines.append(f"# Project: {project_name}")
        lines.append(f"**Project ID:** `{project_id}`")
        lines.append("")

        # Determine stage based on project status
        stage_label = "Planning Stage"
        if dashboard and dashboard.state:
            if dashboard.state.value == "planning":
                stage_label = "Planning Stage"
            elif dashboard.state.value == "ready_for_working":
                stage_label = "Ready for Working"
            elif dashboard.state.value == "in_progress":
                stage_label = "Working Stage"
            elif dashboard.state.value == "completed":
                stage_label = "Completed Stage"
            elif dashboard.state.value == "aborted":
                stage_label = "Aborted Stage"

        lines.append("**Role:** Coordinator")
        lines.append(f"**Status:** {stage_label}")

        # Only show progress information if progress tracking is enabled
        if track_progress:
            lines.append(f"**Progress:** {progress}%")

        lines.append("")

        # Add project description and additional context if available
        if brief and brief.project_description:
            if self.is_context_transfer:
                lines.append("## Knowledge Context")
            else:
                lines.append("## Description")
                
            lines.append(brief.project_description)
            lines.append("")
            
            # In context transfer mode, show additional context in a dedicated section
            if self.is_context_transfer and brief.additional_context:
                lines.append("## Additional Context")
                lines.append(brief.additional_context)
                lines.append("")

        # Add goals section if available and progress tracking is enabled
        if track_progress and brief and brief.goals:
            lines.append("## Goals")
            for goal in brief.goals:
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

        # Add information requests section
        requests = await ProjectManager.get_information_requests(context)
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
                lines.append(f"  **Request ID for resolution:** `{request.request_id}`")
                lines.append("")
        else:
            lines.append("## Information Requests")
            lines.append("No open information requests.")
            lines.append("")

        # Display project ID as invitation information (simplified approach)
        if self.is_context_transfer:
            lines.append("## Share Knowledge Context")
        else:
            lines.append("## Project Invitation")
            
        lines.append("")
        lines.append("### Project ID")
        lines.append(f"**Project ID:** `{project_id}`")
        lines.append("")
        
        if self.is_context_transfer:
            lines.append("**IMPORTANT:** Share this Project ID with anyone who needs to access this knowledge context.")
            lines.append("Recipients can access this knowledge context using:")
            lines.append(f"```\n/join {project_id}\n```")
            lines.append("")
            lines.append("The Project ID never expires and can be used by multiple recipients.")
        else:
            lines.append("**IMPORTANT:** Share this Project ID with all team members.")
            lines.append("Team members can join this project using:")
            lines.append(f"```\n/join {project_id}\n```")
            lines.append("")
            lines.append("The Project ID never expires and can be used by multiple team members.")

        lines.append("")

        return "\n".join(lines)

    async def _format_team_markdown(
        self,
        project_id: str,
        role: ProjectRole,
        brief: Any,
        dashboard: Any,
        context: ConversationContext,
        track_progress: bool,
    ) -> str:
        """Format project information as markdown for Team role"""
        project_name = brief.project_name if brief else "Unnamed Project"
        progress = dashboard.progress_percentage if dashboard and track_progress else 0

        # Build the markdown content
        lines: List[str] = []
        lines.append(f"# Project: {project_name}")
        lines.append(f"**Project ID:** `{project_id}`")
        lines.append("")

        # Determine stage based on project status
        stage_label = "Working Stage"
        if dashboard and dashboard.state:
            if dashboard.state.value == "planning":
                stage_label = "Planning Stage"
            elif dashboard.state.value == "ready_for_working":
                stage_label = "Working Stage"
            elif dashboard.state.value == "in_progress":
                stage_label = "Working Stage"
            elif dashboard.state.value == "completed":
                stage_label = "Completed Stage"
            elif dashboard.state.value == "aborted":
                stage_label = "Aborted Stage"

        lines.append(f"**Role:** Team ({stage_label})")
        lines.append(f"**Status:** {stage_label}")

        # Only show progress information if progress tracking is enabled
        if track_progress:
            lines.append(f"**Progress:** {progress}%")

        lines.append("")

        # Add project description and additional context if available
        if brief and brief.project_description:
            if self.is_context_transfer:
                lines.append("## Knowledge Context")
            else:
                lines.append("## Project Brief")
                
            lines.append(brief.project_description)
            lines.append("")
            
            # In context transfer mode, show additional context in a dedicated section
            if self.is_context_transfer and brief.additional_context:
                lines.append("## Additional Context")
                lines.append(brief.additional_context)
                lines.append("")

        # Add goals section with checkable criteria if progress tracking is enabled
        if track_progress and brief and brief.goals:
            lines.append("## Objectives")
            for goal in brief.goals:
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

        # Add my information requests section
        requests = await ProjectManager.get_information_requests(context)
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

        # Add section for viewing Coordinator conversation
        if self.is_context_transfer:
            lines.append("\n## Knowledge Creator Communication")
            lines.append("Use the `view_coordinator_conversation` tool to see messages from the knowledge creator. Example:")
            lines.append("```")
            lines.append("view_coordinator_conversation(message_count=20)  # Shows last 20 messages")
            lines.append("```")
        else:
            lines.append("\n## Coordinator Communication")
            lines.append("Use the `view_coordinator_conversation` tool to see messages from the Coordinator. Example:")
            lines.append("```")
            lines.append("view_coordinator_conversation(message_count=20)  # Shows last 20 messages")
            lines.append("```")

        return "\n".join(lines)
