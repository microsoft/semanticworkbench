"""
Project Assistant tool functions.

This module defines tool functions for the Project Assistant that can be used
by the LLM during chat completions to proactively assist users.
"""

import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Literal, Optional
from uuid import UUID

import openai_client
from openai.types.chat import ChatCompletionMessageParam
from openai_client.tools import ToolFunctions
from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    MessageSender,
    MessageType,
    NewConversationMessage,
    ParticipantRole,
)
from semantic_workbench_assistant.assistant_app import ConversationContext
from semantic_workbench_assistant.storage import read_model

from .command_processor import (
    handle_add_goal_command,
)
from .config import assistant_config
from .conversation_clients import ConversationClientManager
from .project_data import (
    LogEntryType,
    ProjectInfo,
    ProjectState,
    RequestPriority,
    RequestStatus,
)
from .project_manager import ProjectManager
from .project_storage import (
    ConversationProjectManager,
    ProjectNotifier,
    ProjectRole,
    ProjectStorage,
    ProjectStorageManager,
)
from .utils import load_text_include

logger = logging.getLogger(__name__)


async def invoke_command_handler(
    context: ConversationContext, command_content: str, handler_func: Callable, success_message: str, error_prefix: str
) -> str:
    """
    Create a system message and invoke a command handler function.

    This helper centralizes the pattern of creating a temporary system message
    to reuse command handlers from the chat module.

    Args:
        context: The conversation context
        command_content: The formatted command content
        handler_func: The command handler function to call
        success_message: Message to return on success
        error_prefix: Prefix for error messages

    Returns:
        A string with success or error message
    """
    # Create a temporary system message to invoke the command handler
    temp_message = ConversationMessage(
        id=UUID("00000000-0000-0000-0000-000000000000"),  # Using a placeholder UUID
        content=command_content,
        timestamp=datetime.utcnow(),
        message_type=MessageType.command,
        sender=MessageSender(participant_role=ParticipantRole.assistant, participant_id="system"),
        content_type="text/plain",
        filenames=[],
        metadata={},
        has_debug_data=False,
    )

    try:
        await handler_func(context, temp_message, [])
        return success_message
    except Exception as e:
        logger.exception(f"{error_prefix}: {e}")
        return f"{error_prefix}: {str(e)}"


class Configuration(Enum):
    PROJECT_ASSISTANT = "project_assistant"
    CONTEXT_TRANSFER_ASSISTANT = "context_transfer_assistant"


class ProjectTools:
    """Tools for the Project Assistant to use during chat completions."""

    def __init__(self, context: ConversationContext, role: str):
        """
        Initialize the project tools with the current conversation context.

        Args:
            context: The conversation context
            role: The assistant's role ("coordinator" or "team")
        """
        self.context = context
        self.role = role
        self.tool_functions = ToolFunctions()

        template_id = context.assistant._template_id or "default"
        self.config = (
            Configuration.PROJECT_ASSISTANT if template_id == "default" else Configuration.CONTEXT_TRANSFER_ASSISTANT
        )

        # Register common tools for both roles in both configs
        self.tool_functions.add_function(
            self.get_project_info, "get_project_info", "Get information about the current project state"
        )
        # Common detection tool for both roles
        self.tool_functions.add_function(
            self.suggest_next_action,
            "suggest_next_action",
            "Suggest the next action the user should take based on project state",
        )

        # Register role-specific tools
        if role == "coordinator":
            # Coordinator-specific tools
            self.tool_functions.add_function(
                self.create_project_brief,
                "create_project_brief",
                "Create a project brief with a name and description",
            )
            self.tool_functions.add_function(
                self.resolve_information_request,
                "resolve_information_request",
                "Resolve an information request with information",
            )

            if self.config == Configuration.PROJECT_ASSISTANT:
                self.tool_functions.add_function(
                    self.add_project_goal,
                    "add_project_goal",
                    "Add a goal to the project brief with optional success criteria",
                )
                self.tool_functions.add_function(
                    self.mark_project_ready_for_working,
                    "mark_project_ready_for_working",
                    "Mark the project as ready for working",
                )
        else:
            # Team-specific tools
            self.tool_functions.add_function(
                self.create_information_request,
                "create_information_request",
                "Create an information request for information or to report a blocker",
            )
            self.tool_functions.add_function(
                self.update_project_dashboard,
                "update_project_dashboard",
                "Update the status and progress of the project",
            )
            self.tool_functions.add_function(
                self.mark_criterion_completed, "mark_criterion_completed", "Mark a success criterion as completed"
            )
            self.tool_functions.add_function(
                self.delete_information_request,
                "delete_information_request",
                "Delete an information request that is no longer needed",
            )
            self.tool_functions.add_function(
                self.detect_information_request_needs,
                "detect_information_request_needs",
                "Analyze user message to detect potential information request needs",
            )
            self.tool_functions.add_function(
                self.view_coordinator_conversation,
                "view_coordinator_conversation",
                "View the Coordinator conversation messages to understand the project context and planning discussions",
            )

            if self.config == Configuration.PROJECT_ASSISTANT:
                self.tool_functions.add_function(
                    self.report_project_completion, "report_project_completion", "Report that the project is complete"
                )

    def get_available_tools(self) -> List[str]:
        """
        Get a list of available tools for the current role.

        Returns:
            List of tool names
        """
        return [name for name in self.tool_functions.function_map.keys()]

    async def get_project_info(self, info_type: Literal["all", "brief", "whiteboard", "dashboard", "requests"]) -> str:
        """
        Get information about the current project.

        Args:
            info_type: Type of information to retrieve. Must be one of: all, brief, whiteboard, dashboard, requests.

        Returns:
            Information about the project in a formatted string
        """
        if info_type not in ["all", "brief", "whiteboard", "dashboard", "requests"]:
            return f"Invalid info_type: {info_type}. Must be one of: all, brief, whiteboard, dashboard, requests. Use 'all' to get all information types."

        # Get the project ID for the current conversation
        project_id = await ProjectManager.get_project_id(self.context)
        if not project_id:
            return "No project associated with this conversation. Start by creating a project brief."

        output = []

        # Get project brief if requested
        if info_type in ["all", "brief"]:
            brief = await ProjectManager.get_project_brief(self.context)

            if brief:
                # Format brief information
                output.append(f"## Project Brief: {brief.project_name}")
                output.append(f"\n{brief.project_description}\n")

                if brief.goals:
                    output.append("\n### Goals:\n")

                    for i, goal in enumerate(brief.goals):
                        # Count completed criteria
                        completed = sum(1 for c in goal.success_criteria if c.completed)
                        total = len(goal.success_criteria)

                        output.append(f"{i + 1}. **{goal.name}** - {goal.description}")

                        if goal.success_criteria:
                            output.append(f"   Progress: {completed}/{total} criteria complete")
                            output.append("   Success Criteria:")

                            for j, criterion in enumerate(goal.success_criteria):
                                status = "✅" if criterion.completed else "⬜"
                                output.append(f"   {status} {criterion.description}")

                        output.append("")
                else:
                    # output.append("\n*No goals defined yet.*")
                    pass

        # Get project whiteboard if requested
        if info_type in ["all", "whiteboard"]:
            whiteboard = ProjectStorage.read_project_whiteboard(project_id)

            if whiteboard and whiteboard.content:
                output.append("\n## Project Whiteboard\n")
                output.append(whiteboard.content)
                output.append("")

                if whiteboard.is_auto_generated:
                    output.append("*This whiteboard content is automatically updated by the assistant.*")
                else:
                    output.append("*This whiteboard content has been manually edited.*")

                output.append("")
            elif info_type == "whiteboard":
                output.append("\n## Project Whiteboard\n")
                output.append("*No whiteboard content available yet.*")

        # Get information requests if requested
        if info_type in ["all", "requests"]:
            requests = ProjectStorage.get_all_information_requests(project_id)

            if requests:
                output.append("\n## Information Requests\n")

                # Group requests by status
                active_requests = [r for r in requests if r.status != RequestStatus.RESOLVED]
                resolved_requests = [r for r in requests if r.status == RequestStatus.RESOLVED]

                if active_requests:
                    output.append("### Active Requests")
                    output.append(
                        '\n> 📋 **FOR COORDINATOR AGENTS:** To resolve a request, first get the Request ID below, then use `resolve_information_request(request_id="exact-id-here", resolution="your solution")`. Do NOT use the request title as the ID.\n'
                    )

                    for request in active_requests:
                        priority_marker = {
                            RequestPriority.LOW: "🔹",
                            RequestPriority.MEDIUM: "🔶",
                            RequestPriority.HIGH: "🔴",
                            RequestPriority.CRITICAL: "⚠️",
                        }.get(request.priority, "🔹")

                        # Make the request ID super obvious for resolving requests
                        output.append(f"{priority_marker} **{request.title}** ({request.status.value})")
                        output.append(f"  **Request ID for resolution:** `{request.request_id}`")
                        output.append(f"  Description: {request.description}")

                        if request.updates:
                            last_update = request.updates[-1]
                            output.append(f"  *Last update: {last_update.get('message', '')}*")

                        output.append("")

                if resolved_requests and info_type == "requests":
                    output.append("### Resolved Requests\n")

                    for request in resolved_requests[:5]:  # Show only the 5 most recent
                        output.append(f"✅ **{request.title}** ({request.status.value})")
                        output.append(f"  **Request ID:** `{request.request_id}`")

                        if request.resolution:
                            output.append(f"  Resolution: {request.resolution}")

                        output.append("")
            elif info_type == "requests":
                output.append("\n## Information Requests\n")
                output.append("*No information requests created yet.*")

        # If no data was found for any category
        if not output:
            return "No project information found. Start by creating a project brief."

        return "\n".join(output)

    async def create_project_brief(self, project_name: str, project_description: str) -> str:
        """
        Create a project brief with a name and description.

        Args:
            project_name: The name of the project
            project_description: A description of the project

        Returns:
            A message indicating success or failure
        """
        if self.role != "coordinator":
            return "Only Coordinator can create project briefs."

        # First, make sure we have a project associated with this conversation
        project_id = await ProjectManager.get_project_id(self.context)
        if not project_id:
            return "No project associated with this conversation. Please create a project first."

        # Create a new project brief using ProjectManager
        success, brief = await ProjectManager.create_project_brief(
            context=self.context, project_name=project_name, project_description=project_description
        )

        if success and brief:
            await self.context.send_messages(
                NewConversationMessage(
                    content=f"Project brief '{project_name}' created successfully.",
                    message_type=MessageType.notice,
                    metadata={},  # Add empty metadata
                )
            )
            return f"Project brief '{project_name}' created successfully."
        else:
            return "Failed to create project brief. Please try again."

    async def add_project_goal(self, goal_name: str, goal_description: str, success_criteria: List[str]) -> str:
        """
        Add a goal to the project brief.

        Args:
            goal_name: The name of the goal
            goal_description: A description of the goal
            success_criteria: Optional list of success criteria. If not provided, an empty list will be used.

        Returns:
            A message indicating success or failure
        """
        config = await assistant_config.get(self.context.assistant)
        if not config.track_progress:
            return "Progress tracking is not enabled for this template."

        if self.role != "coordinator":
            return "Only Coordinator can add project goals."

        # Get project ID
        project_id = await ProjectManager.get_project_id(self.context)
        if not project_id:
            return "No project associated with this conversation. Please create a project brief first."

        # Get existing project brief
        brief = await ProjectManager.get_project_brief(self.context)
        if not brief:
            return "No project brief found. Please create one first with create_project_brief."

        # Use the formatted command processor from chat.py to leverage existing functionality
        criteria_str = ""
        if len(success_criteria) > 0:
            criteria_str = "|" + ";".join(success_criteria)

        command_content = f"/add-goal {goal_name}|{goal_description}{criteria_str}"

        return await invoke_command_handler(
            context=self.context,
            command_content=command_content,
            handler_func=handle_add_goal_command,
            success_message=f"Goal '{goal_name}' added to project brief successfully.",
            error_prefix="Error adding goal",
        )

    # Whiteboard methods removed - content is auto-generated

    async def resolve_information_request(self, request_id: str, resolution: str) -> str:
        """
        Resolve an information request with information.

        [COORDINATOR ONLY] This tool is only available to Coordinator agents.

        Args:
            request_id: IMPORTANT! Use the exact Request ID value from get_project_info output
                       (looks like "012345-abcd-67890"), NOT the title of the request
            resolution: Resolution information to add to the request

        Returns:
            A message indicating success or failure
        """
        if self.role != "coordinator":
            # Add more detailed error message with guidance
            error_message = (
                "ERROR: Only Coordinator can resolve information requests. As a Team member, you should use "
                "create_information_request to send requests to the Coordinator, not try to resolve them yourself. "
                "The Coordinator must use resolve_information_request to respond to your requests."
            )
            logger.warning(f"Team member attempted to use resolve_information_request: {request_id}")
            return error_message

        # Get project ID
        project_id = await ProjectManager.get_project_id(self.context)
        if not project_id:
            return "No project associated with this conversation. Unable to resolve information request."

        # Resolve the information request using ProjectManager
        success, information_request = await ProjectManager.resolve_information_request(
            context=self.context, request_id=request_id, resolution=resolution
        )

        if success and information_request:
            # Notification is handled by ProjectManager.resolve_information_request
            return f"Information request '{information_request.title}' has been resolved."
        else:
            logger.warning(f"Failed to resolve information request. Invalid ID provided: '{request_id}'")
            return f'''ERROR: Could not resolve information request with ID "{request_id}".

IMPORTANT STEPS TO RESOLVE INFORMATION REQUESTS:
1. FIRST run get_project_info(info_type="requests") to see the full list of requests
2. Find the request you want to resolve and copy its exact Request ID (looks like "abc123-def-456")
3. Then use resolve_information_request with the EXACT ID from step 2, NOT the title of the request

Example: resolve_information_request(request_id="abc123-def-456", resolution="Your solution here")"'''

    async def create_information_request(
        self, title: str, description: str, priority: Literal["low", "medium", "high", "critical"]
    ) -> str:
        """
        Create an information request to send to the Coordinator for information or to report a blocker.

        This is the MAIN TOOL FOR TEAM MEMBERS to request information, documents, or assistance from the Coordinator.
        Team members should use this tool whenever they need something from the Coordinator.

        Args:
            title: The title of the request (be specific and clear)
            description: A detailed description of what information or help you need from the Coordinator
            priority: The priority of the request. Must be one of: low, medium, high, critical.

        Returns:
            A message indicating success or failure
        """
        if self.role != "team":
            return "Only Team members can create information requests."

        # Get project ID
        project_id = await ProjectManager.get_project_id(self.context)
        if not project_id:
            return "No project associated with this conversation. Unable to create information request."

        # Set default priority if not provided
        if priority is None:
            priority = "medium"

        # Map priority string to enum
        priority_map = {
            "low": RequestPriority.LOW,
            "medium": RequestPriority.MEDIUM,
            "high": RequestPriority.HIGH,
            "critical": RequestPriority.CRITICAL,
        }
        priority_enum = priority_map.get(priority.lower(), RequestPriority.MEDIUM)

        # Create the information request using ProjectManager
        success, request = await ProjectManager.create_information_request(
            context=self.context, title=title, description=description, priority=priority_enum
        )

        if success and request:
            await self.context.send_messages(
                NewConversationMessage(
                    content=f"Information request '{title}' created successfully with {priority} priority. The Coordinator has been notified.",
                    message_type=MessageType.notice,
                    metadata={},  # Add empty metadata
                )
            )
            return f"Information request '{title}' created successfully. The Coordinator has been notified."
        else:
            return "Failed to create information request. Please try again."

    async def update_project_dashboard(
        self,
        status: Literal["planning", "in_progress", "blocked", "completed", "aborted"],
        progress: Optional[int],
        status_message: Optional[str],
        next_actions: Optional[List[str]],
    ) -> str:
        """
        Update the status and progress of the project.

        Args:
            status: The project status. Must be one of: planning, in_progress, blocked, completed, aborted.
            progress: The progress percentage (0-100). If not provided, no progress will be updated.
            status_message: A custom status message. If not provided, no status message will be updated.
            next_actions: A list of next actions. If not provided, no next actions will be updated.

        Returns:
            A message indicating success or failure
        """
        config = await assistant_config.get(self.context.assistant)
        if not config.track_progress:
            return "Progress tracking is not enabled for this template."

        if self.role != "team":
            return "Only Team members can update project dashboard."

        # Get project ID
        project_id = await ProjectManager.get_project_id(self.context)
        if not project_id:
            return "No project associated with this conversation. Unable to update project dashboard."

        # Update the project dashboard using ProjectManager
        success, dashboard = await ProjectManager.update_project_dashboard(
            context=self.context,
            state=status,
            progress=progress,
            status_message=status_message,
            next_actions=next_actions,
        )

        if success and dashboard:
            # Format progress as percentage if available
            progress_text = f" ({progress}% complete)" if progress is not None else ""

            await self.context.send_messages(
                NewConversationMessage(
                    content=f"Project status updated to '{status}'{progress_text}. All project participants will see this update.",
                    message_type=MessageType.notice,
                    metadata={},  # Add empty metadata
                )
            )
            return f"Project status updated to '{status}'{progress_text}."
        else:
            return "Failed to update project dashboard. Please try again."

    async def mark_criterion_completed(self, goal_index: int, criterion_index: int) -> str:
        """
        Mark a success criterion as completed.

        Args:
            goal_index: The index of the goal (0-based)
            criterion_index: The index of the criterion within the goal (0-based)

        Returns:
            A message indicating success or failure
        """
        config = await assistant_config.get(self.context.assistant)
        if not config.track_progress:
            return "Progress tracking is not enabled for this template."

        if self.role != "team":
            return "Only Team members can mark criteria as completed."

        # Get project ID
        project_id = await ProjectManager.get_project_id(self.context)
        if not project_id:
            return "No project associated with this conversation. Unable to mark criterion as completed."

        # Get existing project brief
        brief = await ProjectManager.get_project_brief(self.context)
        if not brief:
            return "No project brief found."

        # Using 0-based indexing directly, no adjustment needed

        # Validate indices
        if goal_index < 0 or goal_index >= len(brief.goals):
            return f"Invalid goal index {goal_index}. Valid indexes are 0 to {len(brief.goals) - 1}. There are {len(brief.goals)} goals."

        goal = brief.goals[goal_index]

        if criterion_index < 0 or criterion_index >= len(goal.success_criteria):
            return f"Invalid criterion index {criterion_index}. Valid indexes for goal '{goal.name}' are 0 to {len(goal.success_criteria) - 1}. Goal '{goal.name}' has {len(goal.success_criteria)} criteria."

        # Update the criterion
        criterion = goal.success_criteria[criterion_index]

        if criterion.completed:
            return f"Criterion '{criterion.description}' is already marked as completed."

        # Get current user information
        participants = await self.context.get_participants()
        current_user_id = None

        for participant in participants.participants:
            if participant.role == "user":
                current_user_id = participant.id
                break

        if not current_user_id:
            return "Could not identify current user."

        # Mark as completed
        criterion.completed = True
        criterion.completed_at = datetime.utcnow()
        criterion.completed_by = current_user_id

        # Update brief metadata
        brief.updated_at = datetime.utcnow()
        brief.updated_by = current_user_id
        brief.version += 1

        # Save the updated brief
        ProjectStorage.write_project_brief(project_id, brief)

        # Log the criterion completion
        await ProjectStorage.log_project_event(
            context=self.context,
            project_id=project_id,
            entry_type=LogEntryType.CRITERION_COMPLETED.value,
            message=f"Success criterion completed: {criterion.description}",
            related_entity_id=None,
            metadata={"goal_name": goal.name, "criterion_description": criterion.description},
        )

        # Update project dashboard
        dashboard = ProjectStorage.read_project_dashboard(project_id)

        if dashboard:
            # Count all completed criteria
            completed_criteria = 0
            total_criteria = 0

            for g in brief.goals:
                total_criteria += len(g.success_criteria)
                completed_criteria += sum(1 for c in g.success_criteria if c.completed)

            # Update dashboard
            dashboard.completed_criteria = completed_criteria
            dashboard.total_criteria = total_criteria

            # Calculate progress percentage
            if total_criteria > 0:
                dashboard.progress_percentage = int((completed_criteria / total_criteria) * 100)

            # Update metadata
            dashboard.updated_at = datetime.utcnow()
            dashboard.updated_by = current_user_id
            dashboard.version += 1

            # Save the updated dashboard
            ProjectStorage.write_project_dashboard(project_id, dashboard)

            # Notify linked conversations with a message
            await ProjectNotifier.notify_project_update(
                context=self.context,
                project_id=project_id,
                update_type="project_dashboard",
                message=f"Success criterion '{criterion.description}' for goal '{goal.name}' has been marked as completed.",
            )

            # Update all project UI inspectors
            await ProjectStorage.refresh_all_project_uis(self.context, project_id)

            # Check if all criteria are completed for project completion
            if completed_criteria == total_criteria and total_criteria > 0:
                await self.context.send_messages(
                    NewConversationMessage(
                        content="🎉 All success criteria have been completed! Consider using the report_project_completion function to formally complete the project.",
                        message_type=MessageType.notice,
                    )
                )

        await self.context.send_messages(
            NewConversationMessage(
                content=f"Success criterion '{criterion.description}' for goal '{goal.name}' has been marked as completed.",
                message_type=MessageType.notice,
            )
        )

        return f"Criterion '{criterion.description}' for goal '{goal.name}' marked as completed."

    async def mark_project_ready_for_working(self) -> str:
        """
        Mark the project as ready for working.
        This is a milestone function that transitions from Planning Stage to Working Stage.

        Returns:
            A message indicating success or failure
        """
        config = await assistant_config.get(self.context.assistant)
        if not config.track_progress:
            return "Progress tracking is not enabled for this template."

        if self.role != "coordinator":
            return "Only Coordinator can mark a project as ready for working."

        # Get project ID
        project_id = await ProjectManager.get_project_id(self.context)
        if not project_id:
            return "No project associated with this conversation. Unable to mark project as ready for working."

        # Get existing project brief and whiteboard
        brief = ProjectStorage.read_project_brief(project_id)
        whiteboard = ProjectStorage.read_project_whiteboard(project_id)

        if not brief:
            return "No project brief found. Please create one before marking as ready for working."

        if not brief.goals:
            return "Project brief has no goals. Please add at least one goal before marking as ready for working."

        # Check if at least one goal has success criteria
        has_criteria = False
        for goal in brief.goals:
            if goal.success_criteria:
                has_criteria = True
                break

        if not has_criteria:
            return "No success criteria defined. Please add at least one success criterion to a goal before marking as ready for working."

        # Check if whiteboard has content
        if not whiteboard or not whiteboard.content:
            return "Project whiteboard is empty. Content will be automatically generated as the project progresses."

        # Get or create project dashboard
        dashboard = ProjectStorage.read_project_dashboard(project_id)

        # Get current user information
        participants = await self.context.get_participants()
        current_user_id = None

        for participant in participants.participants:
            if participant.role == "user":
                current_user_id = participant.id
                break

        if not current_user_id:
            return "Could not identify current user."

        if not dashboard:
            # Create new project info if dashboard doesn't exist
            project_info = ProjectInfo(
                project_id=project_id,
                project_name=brief.project_name if brief else "New Project",
                coordinator_conversation_id=str(self.context.id),
                state=ProjectState.PLANNING,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            ProjectStorage.write_project_info(project_id, project_info)

            # Use project_info directly instead of dashboard
            dashboard = project_info

        # Update state to ready_for_working
        if isinstance(dashboard, dict):
            # Handle the dict case for backward compatibility
            dashboard["state"] = ProjectState.READY_FOR_WORKING
            dashboard["status_message"] = "Project is now ready for team operations"
            dashboard["updated_at"] = datetime.utcnow()
        else:
            # Handle the ProjectInfo case
            dashboard.state = ProjectState.READY_FOR_WORKING
            dashboard.status_message = "Project is now ready for team operations"
            dashboard.updated_at = datetime.utcnow()

        # Save the updated dashboard
        ProjectStorage.write_project_dashboard(project_id, dashboard)

        # Log the milestone transition
        await ProjectStorage.log_project_event(
            context=self.context,
            project_id=project_id,
            entry_type=LogEntryType.MILESTONE_PASSED.value,
            message="Project marked as READY FOR WORKING",
            metadata={"milestone": "ready_for_working"},
        )

        # Notify linked conversations with a message
        await ProjectNotifier.notify_project_update(
            context=self.context,
            project_id=project_id,
            update_type="project_dashboard",
            message="🔔 **Project Milestone Reached**: Coordinator has marked the project as READY FOR WORKING. All project information is now available and you can begin team operations.",
        )

        # Update all project UI inspectors
        await ProjectStorage.refresh_all_project_uis(self.context, project_id)

        await self.context.send_messages(
            NewConversationMessage(
                content="🎯 Project has been marked as READY FOR WORKING. Team members have been notified and can now begin operations.",
                message_type=MessageType.chat,
            )
        )

        return "Project successfully marked as ready for team operations."

    async def report_project_completion(self) -> str:
        """
        Report that the project is complete.
        This is a milestone function that concludes the project lifecycle.

        Returns:
            A message indicating success or failure
        """
        config = await assistant_config.get(self.context.assistant)
        if not config.track_progress:
            return "Progress tracking is not enabled for this template."

        if self.role != "team":
            return "Only Team members can report project completion."

        # Get project ID
        project_id = await ProjectManager.get_project_id(self.context)
        if not project_id:
            return "No project associated with this conversation. Unable to report project completion."

        # Get existing project dashboard
        dashboard = ProjectStorage.read_project_dashboard(project_id)
        if not dashboard:
            return "No project dashboard found. Cannot complete project without a dashboard."

        # Check if all criteria are completed
        if dashboard.completed_criteria < dashboard.total_criteria:
            remaining = dashboard.total_criteria - dashboard.completed_criteria
            return f"Cannot complete project - {remaining} success criteria are still pending completion."

        # Get current user information
        participants = await self.context.get_participants()
        current_user_id = None

        for participant in participants.participants:
            if participant.role == "user":
                current_user_id = participant.id
                break

        if not current_user_id:
            return "Could not identify current user."

        # Update dashboard to completed
        dashboard.state = ProjectState.COMPLETED
        dashboard.progress_percentage = 100
        dashboard.status_message = "Project is now complete"

        # Add lifecycle metadata
        if not hasattr(dashboard, "lifecycle") or not dashboard.lifecycle:
            dashboard.lifecycle = {}

        dashboard.lifecycle["project_completed"] = True
        dashboard.lifecycle["project_completed_time"] = datetime.utcnow().isoformat()
        dashboard.lifecycle["project_completed_by"] = current_user_id

        # Update metadata
        dashboard.updated_at = datetime.utcnow()
        dashboard.updated_by = current_user_id
        dashboard.version += 1

        # Save the updated dashboard
        ProjectStorage.write_project_dashboard(project_id, dashboard)

        # Log the milestone transition
        await ProjectStorage.log_project_event(
            context=self.context,
            project_id=project_id,
            entry_type=LogEntryType.PROJECT_COMPLETED.value,
            message="Project marked as COMPLETED",
            metadata={"milestone": "project_completed"},
        )

        # Notify linked conversations with a message
        await ProjectNotifier.notify_project_update(
            context=self.context,
            project_id=project_id,
            update_type="project_completed",
            message="🎉 **Project Complete**: Team has reported that all project objectives have been achieved. The project is now complete.",
        )

        # Update all project UI inspectors
        await ProjectStorage.refresh_all_project_uis(self.context, project_id)

        await self.context.send_messages(
            NewConversationMessage(
                content="🎉 **Project Complete**: All objectives have been achieved and the project is now complete. The Coordinator has been notified.",
                message_type=MessageType.chat,
            )
        )

        return "Project successfully marked as complete. All participants have been notified."

    async def view_coordinator_conversation(self, message_count: int) -> str:
        """
        View the Coordinator conversation messages for the project.
        This allows Team members to see the context and planning discussions from the Coordinator.

        Args:
            message_count: Number of recent messages to return (between 1-50). Recommend using 20 for a reasonable amount.

        Returns:
            Formatted string containing Coordinator conversation messages
        """
        if self.role != "team":
            return "This tool is only available to Team members."

        # Get project ID
        project_id = await ProjectManager.get_project_id(self.context)
        if not project_id:
            logger.warning("No project ID found for this conversation")
            return "No project associated with this conversation. Unable to view Coordinator conversation."

        # Limit message count to reasonable value
        message_count = min(max(1, message_count), 50)  # Between 1 and 50

        # Get project brief for context
        brief = await ProjectManager.get_project_brief(self.context)
        project_name = brief.project_name if brief else "Project"

        try:
            # Read from shared storage instead of trying cross-conversation API access

            # Read Coordinator conversation messages from shared storage
            coordinator_conversation = ProjectStorage.read_coordinator_conversation(project_id)

            if not coordinator_conversation or not coordinator_conversation.messages:
                logger.warning(f"No Coordinator conversation data found for project {project_id}")
                return f"No Coordinator conversation messages available for {project_name}. Check back later when Coordinator has sent messages."

            # Format the messages for display
            output = []
            output.append(f"# Coordinator Conversation for {project_name}\n")
            output.append(
                "Here are the recent messages from the Coordinator to help you understand the project context:\n"
            )

            # Sort messages by timestamp and limit to the requested count
            messages = sorted(coordinator_conversation.messages, key=lambda m: m.timestamp)
            messages = messages[-message_count:]  # Get the most recent messages

            for msg in messages:
                # Format timestamp
                timestamp = msg.timestamp.strftime("%Y-%m-%d %H:%M")

                # Add formatted message
                output.append(f"### {msg.sender_name} - {timestamp}")
                output.append(f"{msg.content}\n")

            if len(output) <= 3:  # Just the header and note, no actual messages
                return f"No chat messages found in the Coordinator conversation for {project_name}."

            return "\n".join(output)

        except Exception as e:
            logger.exception(f"Error retrieving Coordinator conversation from shared storage: {e}")
            return f"Error retrieving Coordinator conversation: {str(e)}. Please try again later."

    async def delete_information_request(self, request_id: str) -> str:
        """
        Delete an information request that is no longer needed.
        This completely removes the request from the system.

        Args:
            request_id: ID of the request to delete

        Returns:
            Message indicating success or failure
        """
        if self.role != "team":
            return "This tool is only available to Team members."

        # Get project ID
        project_id = await ProjectManager.get_project_id(self.context)
        if not project_id:
            logger.warning("No project ID found for this conversation")
            return "No project associated with this conversation. Unable to delete information request."

        try:
            # Clean the request_id to handle common formatting issues
            cleaned_request_id = request_id.strip().lower()
            # Remove any quotes that might have been added
            cleaned_request_id = cleaned_request_id.replace('"', "").replace("'", "")

            logger.info(f"Original request_id: '{request_id}', Cleaned ID: '{cleaned_request_id}'")

            # Read the information request

            information_request = ProjectStorage.read_information_request(project_id, cleaned_request_id)

            if not information_request:
                # Try to find it in all requests with improved matching algorithm
                all_requests = ProjectStorage.get_all_information_requests(project_id)
                matching_request = None

                # Log available request IDs for debug purposes
                available_ids = [req.request_id for req in all_requests if req.conversation_id == str(self.context.id)]
                logger.info(f"Available request IDs for this conversation: {available_ids}")
                logger.info(f"Looking for request ID: '{cleaned_request_id}'")

                # Try to normalize the request ID to a UUID format
                normalized_id = cleaned_request_id
                # Remove any "uuid:" prefix if present
                if normalized_id.startswith("uuid:"):
                    normalized_id = normalized_id[5:]

                # Check if the ID contains hyphens already, if not try to format it
                if "-" not in normalized_id and len(normalized_id) >= 32:
                    # Try to format in standard UUID format (8-4-4-4-12)
                    try:
                        formatted_id = f"{normalized_id[0:8]}-{normalized_id[8:12]}-{normalized_id[12:16]}-{normalized_id[16:20]}-{normalized_id[20:32]}"
                        logger.info(f"Reformatted ID without hyphens to: {formatted_id}")
                        normalized_id = formatted_id
                    except Exception as e:
                        logger.warning(f"Failed to reformat ID: {e}")

                # For each request, try multiple matching strategies
                for req in all_requests:
                    # Only consider requests from this conversation
                    if req.conversation_id != str(self.context.id):
                        continue

                    # Get string representations of request_id to compare
                    req_id_str = str(req.request_id).lower()
                    req_id_clean = req_id_str.replace("-", "")
                    normalized_id_clean = normalized_id.replace("-", "")

                    logger.debug(f"Comparing against request: {req_id_str}")

                    # Multiple matching strategies, from most specific to least
                    if any([
                        # Exact match
                        req_id_str == normalized_id,
                        # Match ignoring hyphens
                        req_id_clean == normalized_id_clean,
                        # Check for UUID format variations
                        req_id_str == normalized_id.lower(),
                        # Partial match (if one is substring of the other)
                        len(normalized_id) >= 6 and normalized_id in req_id_str,
                        len(req_id_str) >= 6 and req_id_str in normalized_id,
                        # Match on first part of UUID (at least 8 chars)
                        len(normalized_id) >= 8 and normalized_id[:8] == req_id_str[:8] and len(req_id_clean) >= 30,
                    ]):
                        matching_request = req
                        logger.info(f"Found matching request: {req.request_id}, title: {req.title}")
                        break

                if matching_request:
                    information_request = matching_request
                    # Use the actual request_id for future operations
                    request_id = matching_request.request_id
                    logger.info(f"Using matched request ID: {request_id}")
                else:
                    # Log the attempted deletion for debugging
                    logger.warning(
                        f"Failed deletion attempt - request ID '{request_id}' not found in project {project_id}"
                    )
                    # Provide a more helpful error message with available IDs
                    if available_ids:
                        id_examples = ", ".join([f"`{id[:8]}...`" for id in available_ids[:3]])
                        return f"Information request with ID '{request_id}' not found. Your available requests have IDs like: {id_examples}. Please check and try again with the exact ID."
                    else:
                        return f"Information request with ID '{request_id}' not found. You don't have any active requests to delete."

            # Verify ownership - team member can only delete their own requests
            if information_request.conversation_id != str(self.context.id):
                return "You can only delete information requests that you created. This request was created by another conversation."

            # Get current user info for logging
            participants = await self.context.get_participants()
            current_user_id = None
            current_username = None

            for participant in participants.participants:
                if participant.role == "user":
                    current_user_id = participant.id
                    current_username = participant.name
                    break

            if not current_user_id:
                current_user_id = "team-system"
                current_username = "Team Member"

            # Log the deletion before removing the request
            request_title = information_request.title

            # Store the actual request ID from the information_request object for reliable operations
            actual_request_id = information_request.request_id

            # Log the deletion in the project log
            await ProjectStorage.log_project_event(
                context=self.context,
                project_id=project_id,
                entry_type=LogEntryType.REQUEST_DELETED.value,
                message=f"Information request '{request_title}' was deleted by {current_username}",
                related_entity_id=actual_request_id,
                metadata={
                    "request_title": request_title,
                    "deleted_by": current_user_id,
                    "deleted_by_name": current_username,
                },
            )

            # Delete the information request - implementing deletion logic by removing the file
            # Using ProjectStorage instead of direct path access
            # Create information requests directory path and remove the specific file

            request_path = ProjectStorageManager.get_information_request_path(project_id, actual_request_id)
            if request_path.exists():
                request_path.unlink()  # Delete the file

            # Notify Coordinator about the deletion
            try:
                # Get Coordinator conversation ID

                coordinator_dir = ProjectStorageManager.get_project_dir(project_id) / ProjectRole.COORDINATOR.value
                if coordinator_dir.exists():
                    role_file = coordinator_dir / "conversation_role.json"
                    if role_file.exists():
                        role_data = read_model(role_file, ConversationProjectManager.ConversationRoleInfo)
                        if role_data:
                            coordinator_conversation_id = role_data.conversation_id

                            # Notify Coordinator

                            client = ConversationClientManager.get_conversation_client(
                                self.context, coordinator_conversation_id
                            )
                            await client.send_messages(
                                NewConversationMessage(
                                    content=f"Team member ({current_username}) has deleted their request: '{request_title}'",
                                    message_type=MessageType.notice,
                                )
                            )
            except Exception as e:
                logger.warning(f"Could not notify Coordinator about deleted request: {e}")
                # Not critical, so we continue

            # Update all project UI inspectors
            await ProjectStorage.refresh_all_project_uis(self.context, project_id)

            return f"Information request '{request_title}' has been successfully deleted."

        except Exception as e:
            logger.exception(f"Error deleting information request: {e}")
            return f"Error deleting information request: {str(e)}. Please try again later."

    async def detect_information_request_needs(self, message: str) -> Dict[str, Any]:
        """
        Analyze a user message in context of recent chat history to detect potential information request needs.
        Uses an LLM for sophisticated detection, with keyword fallback.

        Args:
            message: The user message to analyze

        Returns:
            Dict with detection results
        """
        # This is Coordinator perspective - not used directly but helps model understanding
        if self.role != "team":
            return {
                "is_information_request": False,
                "reason": "Only Team conversations can create information requests",
            }

        # Use a more sophisticated approach with a language model call

        logger = logging.getLogger(__name__)

        # Check if we're in context transfer mode
        is_context_transfer = False
        try:
            if hasattr(self.context, "assistant") and self.context.assistant is not None:
                # Use the shared config instance from chat.py that has the templates registered
                config = await assistant_config.get(self.context.assistant)
                # In context transfer mode, track_progress is False
                is_context_transfer = not getattr(config, "track_progress", True)
        except Exception as e:
            logger.warning(f"Error determining context transfer mode: {e}")

        # Load appropriate detection prompt based on mode
        if is_context_transfer:
            system_prompt = load_text_include("context_transfer_information_request_detection.txt")
        else:
            system_prompt = load_text_include("project_information_request_detection.txt")

        try:
            # Check if we're in a test environment (Missing parts of context)
            if not hasattr(self.context, "assistant") or self.context.assistant is None:
                return self._simple_keyword_detection(message)

            # Create a simple client for this specific call
            # Note: Using a basic model to keep this detection lightweight

            config = await assistant_config.get(self.context.assistant)

            if not hasattr(config, "service_config"):
                # Fallback to simple detection if service config not available
                return self._simple_keyword_detection(message)

            # Get recent conversation history (up to 10 messages)
            chat_history = []
            try:
                # Get recent messages to provide context
                messages_response = await self.context.get_messages(limit=10)
                if messages_response and messages_response.messages:
                    # Format messages for the LLM
                    for msg in messages_response.messages:
                        # Format the sender name
                        sender_name = "Team Member"
                        if msg.sender.participant_id == self.context.assistant.id:
                            sender_name = "Assistant"

                        # Add to chat history
                        role = "user" if sender_name == "Team Member" else "assistant"
                        chat_history.append({"role": role, "content": f"{sender_name}: {msg.content}"})

                    # Reverse to get chronological order
                    chat_history.reverse()
            except Exception as e:
                logger.warning(f"Could not retrieve chat history: {e}")
                # Continue without history if we can't get it

            # Create chat completion with history context
            async with openai_client.create_client(config.service_config) as client:
                # Prepare messages array with system prompt and chat history
                messages: List[ChatCompletionMessageParam] = [{"role": "system", "content": system_prompt}]

                # Add chat history if available
                if chat_history:
                    for history_msg in chat_history:
                        messages.append({"role": history_msg["role"], "content": history_msg["content"]})

                # Add the current message for analysis - explicitly mark as the latest message
                messages.append({"role": "user", "content": f"Latest message from Team Member: {message}"})

                # Make the API call
                response = await client.chat.completions.create(
                    model="gpt-3.5-turbo",  # Using a smaller, faster model for this analysis
                    messages=messages,
                    response_format={"type": "json_object"},
                    max_tokens=500,
                    temperature=0.2,  # Low temperature for more consistent analysis
                )

                # Extract and parse the response
                if response.choices and response.choices[0].message.content:
                    try:
                        result = json.loads(response.choices[0].message.content)
                        # Add the original message for reference
                        result["original_message"] = message
                        return result
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse JSON from LLM response: {response.choices[0].message.content}")
                        return self._simple_keyword_detection(message)
                else:
                    logger.warning("Empty response from LLM for information request detection")
                    return self._simple_keyword_detection(message)

        except Exception as e:
            # Fallback to simple detection if LLM call fails
            logger.exception(f"Error in LLM-based information request detection: {e}")
            return self._simple_keyword_detection(message)

    def _simple_keyword_detection(self, message: str) -> Dict[str, Any]:
        """
        Simple fallback method for request detection using keyword matching.

        Args:
            message: The user message to analyze

        Returns:
            Dict with detection results
        """
        # Check if we're in context transfer mode (without using async)
        is_context_transfer = False
        try:
            if hasattr(self, "context") and hasattr(self.context, "assistant") and self.context.assistant is not None:
                # Check metadata directly if available
                if hasattr(self.context, "get_conversation"):
                    try:
                        conversation = getattr(self.context, "conversation", None)
                        if conversation and hasattr(conversation, "metadata"):
                            metadata = conversation.metadata or {}
                            assistant_mode = metadata.get("assistant_mode", "")
                            # If we're in context_transfer mode, be more conservative
                            if assistant_mode == "context_transfer":
                                is_context_transfer = True
                    except Exception:
                        pass
        except Exception:
            pass

        # Different indicators based on mode
        if is_context_transfer:
            # More strict indicators for context transfer mode - require clear indicators of missing information
            request_indicators = [
                "not in the context",
                "additional information needed",
                "can't find in the shared knowledge",
                "missing from the context",
                "need information that's not here",
                "the context doesn't cover",
                "knowledge gap",
                "information gap",
                "nothing provided about",
                "no information about",
                "not mentioned anywhere",
                "critical information missing",
            ]
        else:
            # Standard indicators for project mode
            request_indicators = [
                "need information",
                "missing",
                "don't know",
                "unclear",
                "need clarification",
                "help me understand",
                "confused about",
                "what is",
                "how do i",
                "can you explain",
                "request",
                "blocked",
                "problem",
                "issue",
                "question",
                "uncertain",
                "clarify",
            ]

        message_lower = message.lower()
        matched_indicators = [indicator for indicator in request_indicators if indicator in message_lower]

        if not matched_indicators:
            return {"is_information_request": False, "reason": "No information request indicators found in message"}

        # Guess a potential title and description based on the message
        potential_title = ""
        words = message.split()
        if len(words) > 5:
            # Use first 5-7 words as a potential title
            potential_title = " ".join(words[: min(7, len(words))])
            if not potential_title.endswith((".", "?", "!")):
                potential_title += "..."

        # Guess a priority based on urgency keywords
        priority = "medium"
        if any(word in message_lower for word in ["urgent", "critical", "asap", "immediately", "emergency"]):
            priority = "high"
        elif any(word in message_lower for word in ["whenever", "not urgent", "low priority"]):
            priority = "low"

        return {
            "is_information_request": True,
            "matched_indicators": matched_indicators,
            "potential_title": potential_title,
            "potential_description": message,
            "suggested_priority": priority,
            "confidence": 0.6,  # Medium confidence for keyword-based detection
        }

    async def suggest_next_action(self) -> Dict[str, Any]:
        """
        Suggest the next action the user should take based on project state.

        Returns:
            Dict with suggestion details
        """
        # Get project ID
        project_id = await ProjectManager.get_project_id(self.context)
        if not project_id:
            logger.warning("No project ID found for this conversation")
            return {
                "suggestion": "no_project",
                "reason": "No project associated with this conversation. Unable to suggest next action.",
                "priority": "low",
                "function": None,
            }

        project_info = ProjectStorage.read_project_info(project_id)
        if not project_info:
            return {
                "suggestion": "no_project_info",
                "reason": "No project information found. Unable to suggest next action.",
                "priority": "low",
                "function": None,
            }

        # Get project state information
        brief = ProjectStorage.read_project_brief(project_id)
        requests = ProjectStorage.get_all_information_requests(project_id)

        # Check if project brief exists
        if not brief:
            if self.role == "coordinator":
                return {
                    "suggestion": "create_project_brief",
                    "reason": "No project brief found. Start by creating one.",
                    "priority": "high",
                    "function": "create_project_brief",
                    "parameters": {"project_name": "", "project_description": ""},
                }
            else:
                return {
                    "suggestion": "wait_for_coordinator",
                    "reason": "No project brief found. The Coordinator needs to create one before you can proceed.",
                    "priority": "medium",
                    "function": None,
                }

        # Check if goals exist
        if self.config == Configuration.PROJECT_ASSISTANT:
            if not brief.goals:
                if self.role == "coordinator":
                    return {
                        "suggestion": "add_project_goal",
                        "reason": "Project brief has no goals. Add at least one goal with success criteria.",
                        "priority": "high",
                        "function": "add_project_goal",
                        "parameters": {"goal_name": "", "goal_description": "", "success_criteria": []},
                    }
                else:
                    return {
                        "suggestion": "wait_for_goals",
                        "reason": "Project brief has no goals. The Coordinator needs to add goals before you can proceed.",
                        "priority": "medium",
                        "function": None,
                    }

        # Check project info if project is ready for working
        ready_for_working = project_info.state == ProjectState.READY_FOR_WORKING

        if not ready_for_working and self.role == "coordinator":
            # Check if it's ready to mark as ready for working
            if self.config == Configuration.CONTEXT_TRANSFER_ASSISTANT:
                has_goals = True
                has_criteria = True
            else:
                has_goals = bool(brief.goals)
                has_criteria = any(bool(goal.success_criteria) for goal in brief.goals)

            if has_goals and has_criteria:
                return {
                    "suggestion": "mark_ready_for_working",
                    "reason": "Project information is complete. Mark it as ready for team operations.",
                    "priority": "medium",
                    "function": "mark_project_ready_for_working",
                    "parameters": {},
                }

        # Check for unresolved information requests for Coordinator
        if self.role == "coordinator":
            active_requests = [r for r in requests if r.status == RequestStatus.NEW]
            if active_requests:
                request = active_requests[0]  # Get the first unresolved request
                return {
                    "suggestion": "resolve_information_request",
                    "reason": f"There are {len(active_requests)} unresolved information requests. Consider resolving '{request.title}'.",
                    "priority": "high"
                    if request.priority in [RequestPriority.HIGH, RequestPriority.CRITICAL]
                    else "medium",
                    "function": "resolve_information_request",
                    "parameters": {"request_id": request.request_id, "resolution": ""},
                }

        # For team, check if all criteria are completed for project completion
        criteria = await ProjectManager.get_project_criteria(self.context)
        incomplete_criteria = [criterion for criterion in criteria if not criterion.completed]

        if self.role == "team" and not incomplete_criteria:
            return {
                "suggestion": "report_project_completion",
                "reason": "All success criteria have been completed. Report project completion.",
                "priority": "medium",
                "function": "report_project_completion",
                "parameters": {},
            }

        # For team, suggest marking criteria as completed if any are pending
        if self.role == "team" and incomplete_criteria:
            # Find the first uncompleted criterion
            for goal_index, goal in enumerate(brief.goals):
                for criterion_index, criterion in enumerate(goal.success_criteria):
                    if not criterion.completed:
                        return {
                            "suggestion": "mark_criterion_completed",
                            "reason": "Update progress by marking completed success criteria.",
                            "priority": "low",
                            "function": "mark_criterion_completed",
                            "parameters": {
                                "goal_index": goal_index,  # 0-based indexing
                                "criterion_index": criterion_index,  # 0-based indexing
                            },
                        }

        # Default suggestions based on role
        if self.role == "coordinator":
            return {
                "suggestion": "monitor_progress",
                "reason": "Monitor team operations and respond to any new information requests.",
                "priority": "low",
                "function": None,
            }
        else:
            return {
                "suggestion": "update_status",
                "reason": "Continue team operations and update project progress as you make advancements.",
                "priority": "low",
                "function": "update_project_dashboard",
                "parameters": {"status": "in_progress"},
            }
