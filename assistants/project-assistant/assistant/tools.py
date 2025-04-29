"""
Project Assistant tool functions.

This module defines tool functions for the Project Assistant that can be used
by the LLM during chat completions to proactively assist users.
"""

from datetime import datetime
from typing import Any, Callable, Dict, List, Literal, Optional
from uuid import UUID

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
from .conversation_clients import ConversationClientManager
from .conversation_project_link import ConversationProjectManager
from .logging import logger
from .project_common import ConfigurationTemplate
from .project_data import (
    LogEntryType,
    Project,
    ProjectInfo,
    ProjectState,
    RequestPriority,
    RequestStatus,
)
from .project_manager import ProjectManager
from .project_notifications import ProjectNotifier
from .project_storage import ProjectStorage, ProjectStorageManager
from .project_storage_models import ConversationRole
from .utils import is_context_transfer_assistant


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


class ProjectTools:
    """Tools for the Project Assistant to use during chat completions."""

    def __init__(self, context: ConversationContext, role: ConversationRole):
        """
        Initialize the project tools with the current conversation context.

        Args:
            context: The conversation context
            role: The assistant's role (ConversationRole enum)
        """
        self.context = context
        self.role = role
        self.tool_functions = ToolFunctions()
        self.is_context_transfer = is_context_transfer_assistant(context)

        template_id = context.assistant._template_id or "default"
        self.config_template = (
            ConfigurationTemplate.PROJECT_ASSISTANT
            if template_id == "default"
            else ConfigurationTemplate.CONTEXT_TRANSFER_ASSISTANT
        )

        # Register common tools for both roles in both configs
        self.tool_functions.add_function(
            self.get_project_info, "get_project_info", "Get information about the current project state"
        )

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

            if self.config_template == ConfigurationTemplate.PROJECT_ASSISTANT:
                self.tool_functions.add_function(
                    self.add_project_goal,
                    "add_project_goal",
                    "Add a goal to the project brief with optional success criteria",
                )
                self.tool_functions.add_function(
                    self.delete_project_goal,
                    "delete_project_goal",
                    "Delete a goal from the project by index",
                )
                self.tool_functions.add_function(
                    self.mark_project_ready_for_working,
                    "mark_project_ready_for_working",
                    "Mark the project as ready for working",
                )
        else:
            # Team-specific tools
            self.tool_functions.add_function(
                self.update_project_status,
                "update_project_status",
                "Update the status and progress of the project",
            )
            # detect_information_request_needs is used automatically by the system
            # and should not be exposed directly as an LLM tool
            self.tool_functions.add_function(
                self.create_information_request,
                "create_information_request",
                "Create an information request for information or to report a blocker",
            )
            self.tool_functions.add_function(
                self.delete_information_request,
                "delete_information_request",
                "Delete an information request that is no longer needed",
            )
            self.tool_functions.add_function(
                self.view_coordinator_conversation,
                "view_coordinator_conversation",
                "View the Coordinator conversation messages to understand the project context and planning discussions",
            )
            self.tool_functions.add_function(
                self.mark_criterion_completed, "mark_criterion_completed", "Mark a success criterion as completed"
            )

            if self.config_template == ConfigurationTemplate.PROJECT_ASSISTANT:
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

    async def get_project_info(self) -> Project | None:
        """
        Get information about the current project.

        Args:
            none

        Returns:
            Information about the project in a formatted string
        """

        project_id = await ProjectManager.get_project_id(self.context)
        if not project_id:
            return None

        project = await ProjectManager.get_project(self.context)
        if not project:
            return None

        return project

    async def update_project_status(
        self,
        status: Literal["planning", "in_progress", "blocked", "completed", "aborted"],
        progress: Optional[int],
        status_message: Optional[str],
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

        if self.role is not ConversationRole.TEAM:
            return "Only Team members can update project status."

        # Get project ID
        project_id = await ProjectManager.get_project_id(self.context)
        if not project_id:
            return "No project associated with this conversation. Unable to update project status."

        # Update the project info using ProjectManager
        project_info = await ProjectManager.update_project_info(
            context=self.context,
            state=status,
            status_message=status_message,
        )

        if project_info:
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
            return "Failed to update project status. Please try again."

    async def create_project_brief(self, project_name: str, project_description: str) -> str:
        """
        Create a project brief with a name and description.

        Args:
            project_name: The name of the project
            project_description: A description of the project

        Returns:
            A message indicating success or failure
        """
        if self.role is not ConversationRole.COORDINATOR:
            return "Only Coordinator can create project briefs."

        # First, make sure we have a project associated with this conversation
        project_id = await ProjectManager.get_project_id(self.context)
        if not project_id:
            return "No project associated with this conversation. Please create a project first."

        # Create a new project brief using ProjectManager
        brief = await ProjectManager.update_project_brief(
            context=self.context,
            project_name=project_name,
            project_description=project_description,
            send_notification=True,
        )

        if brief:
            await self.context.send_messages(
                NewConversationMessage(
                    content=f"Project brief '{project_name}' updated successfully.",
                    message_type=MessageType.notice,
                    metadata={"debug": brief.model_dump()},
                )
            )
            return f"Project brief '{project_name}' updated successfully."
        else:
            return "Failed to update project brief. Please try again."

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
        if self.role is not ConversationRole.COORDINATOR:
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
        if self.role is not ConversationRole.TEAM:
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

    async def delete_information_request(self, request_id: str) -> str:
        """
        Delete an information request that is no longer needed.
        This completely removes the request from the system.

        Args:
            request_id: ID of the request to delete

        Returns:
            Message indicating success or failure
        """
        if self.role is not ConversationRole.TEAM:
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

                coordinator_dir = ProjectStorageManager.get_project_dir(project_id) / ConversationRole.COORDINATOR.value
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

    async def add_project_goal(self, goal_name: str, goal_description: str, success_criteria: List[str]) -> str:
        """
        Add a goal to the project.

        Args:
            goal_name: The name of the goal
            goal_description: A description of the goal
            success_criteria: Optional list of success criteria. If not provided, an empty list will be used.

        Returns:
            A message indicating success or failure
        """

        if self.role is not ConversationRole.COORDINATOR:
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
        
    async def delete_project_goal(self, goal_index: int) -> str:
        """
        Delete a goal from the project by index.
        
        Args:
            goal_index: The index of the goal to delete (0-based)
            
        Returns:
            A message indicating success or failure
        """
        
        if self.role is not ConversationRole.COORDINATOR:
            return "Only Coordinator can delete project goals."
            
        # Get project ID - validate project exists
        project_id = await ProjectManager.get_project_id(self.context)
        if not project_id:
            return "No project associated with this conversation."
            
        # Call the ProjectManager method to delete the goal
        success, result = await ProjectManager.delete_project_goal(
            context=self.context,
            goal_index=goal_index,
        )
        
        if success:
            # Notify the user about the successful deletion
            await self.context.send_messages(
                NewConversationMessage(
                    content=f"Goal '{result}' has been successfully deleted from the project.", 
                    message_type=MessageType.notice,
                )
            )
            return f"Goal '{result}' has been successfully deleted from the project."
        else:
            # Return the error message
            return f"Error deleting goal: {result}"

    async def mark_criterion_completed(self, goal_index: int, criterion_index: int) -> str:
        """
        Mark a success criterion as completed.

        Args:
            goal_index: The index of the goal (0-based)
            criterion_index: The index of the criterion within the goal (0-based)

        Returns:
            A message indicating success or failure
        """

        if self.role is not ConversationRole.TEAM:
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

        # Get the project to access goals
        project = ProjectStorage.read_project(project_id)
        if not project or not project.goals:
            return "No project goals found."

        # Validate indices
        if goal_index < 0 or goal_index >= len(project.goals):
            return f"Invalid goal index {goal_index}. Valid indexes are 0 to {len(project.goals) - 1}. There are {len(project.goals)} goals."

        goal = project.goals[goal_index]

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

        # Save the updated project with the completed criterion
        ProjectStorage.write_project(project_id, project)

        # Log the criterion completion
        await ProjectStorage.log_project_event(
            context=self.context,
            project_id=project_id,
            entry_type=LogEntryType.CRITERION_COMPLETED.value,
            message=f"Success criterion completed: {criterion.description}",
            related_entity_id=None,
            metadata={"goal_name": goal.name, "criterion_description": criterion.description},
        )

        # Update project info
        project_info = ProjectStorage.read_project_info(project_id)

        if project_info:
            # Count all completed criteria
            completed_criteria = 0
            total_criteria = 0

            # Get the project to access goals
            project = ProjectStorage.read_project(project_id)
            if project and project.goals:
                for g in project.goals:
                    total_criteria += len(g.success_criteria)
                    completed_criteria += sum(1 for c in g.success_criteria if c.completed)

            # Update project info with criteria stats
            project_info.completed_criteria = completed_criteria
            project_info.total_criteria = total_criteria

            # Calculate progress percentage
            if total_criteria > 0:
                project_info.progress_percentage = int((completed_criteria / total_criteria) * 100)

            # Update metadata
            project_info.updated_at = datetime.utcnow()
            project_info.updated_by = current_user_id
            project_info.version += 1

            # Save the updated project info
            ProjectStorage.write_project_info(project_id, project_info)

            # Notify linked conversations with a message
            await ProjectNotifier.notify_project_update(
                context=self.context,
                project_id=project_id,
                update_type="project_info",
                message=f"Success criterion '{criterion.description}' for goal '{goal.name}' has been marked as completed.",
            )

            # Update all project UI inspectors
            await ProjectStorage.refresh_all_project_uis(self.context, project_id)

            # Check if all criteria are completed for project completion
            # Count all completed criteria again to check for completion
            completed = 0
            total = 0

            # Get the project to access goals
            project = ProjectStorage.read_project(project_id)
            if project and project.goals:
                for g in project.goals:
                    total += len(g.success_criteria)
                    completed += sum(1 for c in g.success_criteria if c.completed)

            if completed == total and total > 0:
                # Automatically complete the project
                success, project_info = await ProjectManager.complete_project(
                    context=self.context,
                    summary=f"All {total} success criteria have been completed! Project has been automatically marked as complete.",
                )

                if success:
                    await self.context.send_messages(
                        NewConversationMessage(
                            content="🎉 All success criteria have been completed! The project has been automatically marked as complete.",
                            message_type=MessageType.notice,
                        )
                    )
                else:
                    await self.context.send_messages(
                        NewConversationMessage(
                            content="🎉 All success criteria have been completed! Would you like me to formally complete the project?",
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

        if self.role is not ConversationRole.COORDINATOR:
            return "Only Coordinator can mark a project as ready for working."

        # Get project ID
        project_id = await ProjectManager.get_project_id(self.context)
        if not project_id:
            return "No project associated with this conversation. Unable to mark project as ready for working."

        # Get existing project brief, whiteboard, and project
        brief = ProjectStorage.read_project_brief(project_id)
        whiteboard = ProjectStorage.read_project_whiteboard(project_id)
        project = ProjectStorage.read_project(project_id)

        if not brief:
            return "No project brief found. Please create one before marking as ready for working."

        if not project or not project.goals:
            return "Project has no goals. Please add at least one goal before marking as ready for working."

        # Check if at least one goal has success criteria
        has_criteria = False
        for goal in project.goals:
            if goal.success_criteria:
                has_criteria = True
                break

        if not has_criteria:
            return "No success criteria defined. Please add at least one success criterion to a goal before marking as ready for working."

        # Check if whiteboard has content
        if not whiteboard or not whiteboard.content:
            return "Project whiteboard is empty. Content will be automatically generated as the project progresses."

        # Get or create project info
        project_info = ProjectStorage.read_project_info(project_id)

        # Get current user information
        participants = await self.context.get_participants()
        current_user_id = None

        for participant in participants.participants:
            if participant.role == "user":
                current_user_id = participant.id
                break

        if not current_user_id:
            return "Could not identify current user."

        if not project_info:
            # Create new project info if it doesn't exist
            project_info = ProjectInfo(
                project_id=project_id,
                coordinator_conversation_id=str(self.context.id),
                state=ProjectState.PLANNING,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

        # Update state to ready_for_working
        if isinstance(project_info, dict):
            # Handle the dict case for backward compatibility
            project_info["state"] = ProjectState.READY_FOR_WORKING
            project_info["status_message"] = "Project is now ready for team operations"
            project_info["updated_at"] = datetime.utcnow()
        else:
            # Handle the ProjectInfo case
            project_info.state = ProjectState.READY_FOR_WORKING
            project_info.status_message = "Project is now ready for team operations"
            project_info.updated_at = datetime.utcnow()

        # Save the updated project info
        ProjectStorage.write_project_info(project_id, project_info)

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
            update_type="project_info",
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

        if self.role is not ConversationRole.TEAM:
            return "Only Team members can report project completion."

        # Get project ID
        project_id = await ProjectManager.get_project_id(self.context)
        if not project_id:
            return "No project associated with this conversation. Unable to report project completion."

        # Get existing project info
        project_info = ProjectStorage.read_project_info(project_id)
        if not project_info:
            return "No project information found. Cannot complete project without project information."

        # Check if all criteria are completed
        if getattr(project_info, "completed_criteria", 0) < getattr(project_info, "total_criteria", 0):
            remaining = project_info.total_criteria - project_info.completed_criteria
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

        # Update project info to completed
        project_info.state = ProjectState.COMPLETED
        project_info.progress_percentage = 100
        project_info.status_message = "Project is now complete"

        # Add lifecycle metadata
        if not hasattr(project_info, "lifecycle") or not project_info.lifecycle:
            project_info.lifecycle = {}

        project_info.lifecycle["project_completed"] = True
        project_info.lifecycle["project_completed_time"] = datetime.utcnow().isoformat()
        project_info.lifecycle["project_completed_by"] = current_user_id

        # Update metadata
        project_info.updated_at = datetime.utcnow()
        project_info.updated_by = current_user_id
        project_info.version += 1

        # Save the updated project info
        ProjectStorage.write_project_info(project_id, project_info)

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
        if self.role is not ConversationRole.TEAM:
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
        project = ProjectStorage.read_project(project_id)
        requests = ProjectStorage.get_all_information_requests(project_id)

        # Check if project brief exists
        if not brief:
            if self.role is ConversationRole.COORDINATOR:
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
        if self.config_template == ConfigurationTemplate.PROJECT_ASSISTANT:
            if not project or not project.goals:
                if self.role is ConversationRole.COORDINATOR:
                    return {
                        "suggestion": "add_project_goal",
                        "reason": "Project has no goals. Add at least one goal with success criteria.",
                        "priority": "high",
                        "function": "add_project_goal",
                        "parameters": {"goal_name": "", "goal_description": "", "success_criteria": []},
                    }
                else:
                    return {
                        "suggestion": "wait_for_goals",
                        "reason": "Project has no goals. The Coordinator needs to add goals before you can proceed.",
                        "priority": "medium",
                        "function": None,
                    }

        # Check project info if project is ready for working
        ready_for_working = project_info.state == ProjectState.READY_FOR_WORKING

        if not ready_for_working and self.role is ConversationRole.COORDINATOR:
            # Check if it's ready to mark as ready for working
            if self.config_template == ConfigurationTemplate.CONTEXT_TRANSFER_ASSISTANT:
                has_goals = True
                has_criteria = True
            else:
                has_goals = bool(project and project.goals)
                has_criteria = bool(
                    project and project.goals and any(bool(goal.success_criteria) for goal in project.goals)
                )

            if has_goals and has_criteria:
                return {
                    "suggestion": "mark_ready_for_working",
                    "reason": "Project information is complete. Mark it as ready for team operations.",
                    "priority": "medium",
                    "function": "mark_project_ready_for_working",
                    "parameters": {},
                }

        # Check for unresolved information requests for Coordinator
        if self.role is ConversationRole.COORDINATOR:
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

        if self.role is ConversationRole.TEAM and not incomplete_criteria:
            return {
                "suggestion": "report_project_completion",
                "reason": "All success criteria have been completed. Report project completion.",
                "priority": "medium",
                "function": "report_project_completion",
                "parameters": {},
            }

        # For team, suggest marking criteria as completed if any are pending
        if self.role is ConversationRole.TEAM and incomplete_criteria:
            # Get the project to access goals
            project = ProjectStorage.read_project(project_id)
            if project and project.goals:
                # Find the first uncompleted criterion
                for goal_index, goal in enumerate(project.goals):
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
        if self.role is ConversationRole.COORDINATOR:
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
                "function": "update_project_info",
                "parameters": {"status": "in_progress"},
            }
