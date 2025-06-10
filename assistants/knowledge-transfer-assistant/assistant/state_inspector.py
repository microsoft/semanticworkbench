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

from .common import detect_assistant_role
from .conversation_project_link import ConversationKnowledgePackageManager
from .data import RequestStatus
from .manager import KnowledgeTransferManager
from .storage import ProjectStorage
from .storage_models import ConversationRole

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

    # Default display name and description
    display_name = "Status"
    description = ""

    def __init__(self, config_provider) -> None:
        self.config_provider = config_provider

    async def is_enabled(self, context: ConversationContext) -> bool:
        return True

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        """
        Get project information for display in the inspector panel.
        """

        # State variables that will determine the content to display.
        conversation_role = await detect_assistant_role(context)

        self.display_name = "Knowledge Overview"
        self.description = "Information about the knowledge space."

        # Determine the conversation's role and project
        project_id = await ConversationKnowledgePackageManager.get_associated_project_id(context)
        if not project_id:
            return AssistantConversationInspectorStateDataModel(
                data={"content": "No active project. Start a conversation to create one."}
            )

        # Get project information
        brief = await KnowledgeTransferManager.get_project_brief(context)
        project_info = await KnowledgeTransferManager.get_project_info(context)

        if conversation_role == ConversationRole.COORDINATOR:
            markdown = await self._format_coordinator_markdown(
                project_id, conversation_role, brief, project_info, context
            )
        else:
            markdown = await self._format_team_markdown(project_id, conversation_role, brief, project_info, context)

        return AssistantConversationInspectorStateDataModel(data={"content": markdown})

    async def _format_coordinator_markdown(
        self,
        project_id: str,
        role: ConversationRole,
        brief: Any,
        project_info: Any,
        context: ConversationContext,
    ) -> str:
        """Format project information as markdown for Coordinator role"""

        lines: List[str] = []

        # Get the project
        project = ProjectStorage.read_project(project_id)

        lines.append("**Role:** Coordinator")

        # stage_label = "Planning Stage"
        # if project_info and project_info.state:
        #     if project_info.state.value == "planning":
        #         stage_label = "Planning Stage"
        #     elif project_info.state.value == "ready_for_working":
        #         stage_label = "Ready for Working"
        #     elif project_info.state.value == "in_progress":
        #         stage_label = "Working Stage"
        #     elif project_info.state.value == "achieved":
        #         stage_label = "Completed Stage"
        #     elif project_info.state.value == "aborted":
        #         stage_label = "Aborted Stage"
        # lines.append(f"**Status:** {stage_label}")

        if project_info and project_info.status_message:
            lines.append(f"**Status Message:** {project_info.status_message}")

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

        # Add goals section if available and progress tracking is enabled
        if project and project.learning_objectives:
            lines.append("## Goals")
            for goal in project.learning_objectives:
                criteria_complete = sum(1 for c in goal.learning_outcomes if c.achieved)
                criteria_total = len(goal.learning_outcomes)
                lines.append(f"### {goal.name}")
                lines.append(goal.description)
                lines.append(f"**Progress:** {criteria_complete}/{criteria_total} criteria complete")

                if goal.learning_outcomes:
                    lines.append("")
                    lines.append("#### Success Criteria:")
                    for criterion in goal.learning_outcomes:
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
        project_info = await KnowledgeTransferManager.get_project_info(context, project_id)
        share_url = project_info.share_url if project_info else None
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
        project_id: str,
        role: ConversationRole,
        brief: Any,
        project_info: Any,
        context: ConversationContext,
    ) -> str:
        """Format project information as markdown for Team role"""

        lines: List[str] = []

        # Get the project
        project = ProjectStorage.read_project(project_id)

        lines.append("**Role:** Team")

        # Determine stage based on project status
        # stage_label = "Working Stage"
        # if project_info and project_info.state:
        #     if project_info.state.value == "planning":
        #         stage_label = "Planning Stage"
        #     elif project_info.state.value == "ready_for_working":
        #         stage_label = "Working Stage"
        #     elif project_info.state.value == "in_progress":
        #         stage_label = "Working Stage"
        #     elif project_info.state.value == "achieved":
        #         stage_label = "Completed Stage"
        #     elif project_info.state.value == "aborted":
        #         stage_label = "Aborted Stage"
        # lines.append(f"**Status:** {stage_label}")

        # Add status message if available
        if project_info and project_info.status_message:
            lines.append(f"**Status Message:** {project_info.status_message}")

        lines.append("")

        # Add project description and additional context if available
        lines.append("## Brief")

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

        # Add goals section with checkable criteria if progress tracking is enabled
        if project and project.learning_objectives:
            lines.append("## Objectives")
            for goal in project.learning_objectives:
                criteria_complete = sum(1 for c in goal.learning_outcomes if c.achieved)
                criteria_total = len(goal.learning_outcomes)
                lines.append(f"### {goal.name}")
                lines.append(goal.description)
                lines.append(f"**Progress:** {criteria_complete}/{criteria_total} criteria complete")

                if goal.learning_outcomes:
                    lines.append("")
                    lines.append("#### Success Criteria:")
                    for criterion in goal.learning_outcomes:
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
