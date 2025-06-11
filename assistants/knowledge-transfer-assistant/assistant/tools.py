"""
Knowledge Transfer Assistant tool functions.

This module defines tool functions for the Knowledge Transfer Assistant that can be used
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
from .conversation_project_link import ConversationKnowledgePackageManager
from .data import (
    KnowledgePackageInfo,
    KnowledgeTransferState,
    LogEntryType,
    RequestPriority,
    RequestStatus,
)
from .logging import logger
from .manager import KnowledgeTransferManager
from .notifications import ProjectNotifier
from .storage import ProjectStorage, ProjectStorageManager
from .storage_models import ConversationRole


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

        # self.tool_functions.add_function(
        #     self.suggest_next_action,
        #     "suggest_next_action",
        #     "Suggest the next action the user should take based on project state",
        # )

        # Register role-specific tools
        if role == "coordinator":
            # Coordinator-specific tools
            self.tool_functions.add_function(
                self.update_brief,
                "update_brief",
                "Update a brief with a title and description",
            )
            self.tool_functions.add_function(
                self.resolve_information_request,
                "resolve_information_request",
                "Resolve an information request with information",
            )

            # self.tool_functions.add_function(
            #     self.add_project_goal,
            #     "add_project_goal",
            #     "Add a goal to the project brief with optional success criteria",
            # )
            # self.tool_functions.add_function(
            #     self.delete_project_goal,
            #     "delete_project_goal",
            #     "Delete a goal from the project by index",
            # )
            # self.tool_functions.add_function(
            #     self.mark_project_ready_for_working,
            #     "mark_project_ready_for_working",
            #     "Mark the project as ready for working",
            # )

        else:
            # Team-specific tools

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

            # self.tool_functions.add_function(
            #     self.update_project_status,
            #     "update_project_status",
            #     "Update the status and progress of the project",
            # )
            # self.tool_functions.add_function(
            #     self.report_project_completion, "report_project_completion", "Report that the project is complete"
            # )
            # self.tool_functions.add_function(
            #     self.mark_criterion_completed, "mark_criterion_completed", "Mark a success criterion as completed"
            # )

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
        project_id = await KnowledgeTransferManager.get_project_id(self.context)
        if not project_id:
            return "No project associated with this conversation. Unable to update project status."

        # Update the project info using KnowledgeTransferManager
        project_info = await KnowledgeTransferManager.update_project_info(
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

    async def update_brief(self, title: str, description: str) -> str:
        """
        Update a brief with a title and description.

        Args:
            title: The title of the brief
            description: A description of the context bundle or project

        Returns:
            A message indicating success or failure
        """
        if self.role is not ConversationRole.COORDINATOR:
            return "Only Coordinator can create project briefs."

        # First, make sure we have a project associated with this conversation
        project_id = await KnowledgeTransferManager.get_project_id(self.context)
        if not project_id:
            return "No project associated with this conversation. Please create a project first."

        # Create a new project brief using KnowledgeTransferManager
        brief = await KnowledgeTransferManager.update_project_brief(
            context=self.context,
            title=title,
            description=description,
            send_notification=True,
        )

        if brief:
            await self.context.send_messages(
                NewConversationMessage(
                    content=f"Brief '{title}' updated successfully.",
                    message_type=MessageType.notice,
                    metadata={"debug": brief.model_dump()},
                )
            )
            return f"Brief '{title}' updated successfully."
        else:
            return "Failed to update the brief. Please try again."

    async def resolve_information_request(self, request_id: str, resolution: str) -> str:
        """
        Resolve an information request when you have the needed information to address it. Only use for active information requests. If there are no active information requests, this should never be called.

        WHEN TO USE:
        - When you have information that directly answers a team member's request
        - When the user has supplied information that resolves a pending request
        - When you've gathered enough details to unblock a team member
        - When a request is no longer relevant and should be closed with explanation

        IMPORTANT WORKFLOW:
        1. ALWAYS call get_project_info(info_type="requests") first to see all pending requests
        2. Identify the request you want to resolve and find its exact Request ID
        3. Use the exact ID in your request_id parameter - not the title
        4. Provide a clear resolution that addresses the team member's needs

        Args:
            request_id: IMPORTANT! Use the exact Request ID value from get_project_info output
                       (looks like "012345-abcd-67890"), NOT the title of the request
            resolution: Complete information that addresses the team member's question or blocker

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
        project_id = await KnowledgeTransferManager.get_project_id(self.context)
        if not project_id:
            return "No project associated with this conversation. Unable to resolve information request."

        # Resolve the information request using KnowledgeTransferManager
        success, information_request = await KnowledgeTransferManager.resolve_information_request(
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
        Create an information request to send to the Coordinator for information that is unavailable to you or to report a blocker.

        WHEN TO USE:
        - When you need specific information or clarification from the Coordinator
        - When encountering a blocker that prevents progress on a goal
        - When requesting additional resources or documentation
        - When you need a decision from the project Coordinator
        - When a user expressly asks for information or help with something unclear

        Set an appropriate priority based on how critical the information is:
        - "low": Nice to have, not blocking progress
        - "medium": Important but not immediate
        - "high": Important and somewhat urgent
        - "critical": Completely blocked, cannot proceed without this information

        Args:
            title: A concise, clear title that summarizes what information is needed
            description: A detailed explanation of what information is needed and why it's important
            priority: The priority level - must be one of: low, medium, high, critical

        Returns:
            A message indicating success or failure
        """
        if self.role is not ConversationRole.TEAM:
            return "Only Team members can create information requests."

        # Get project ID
        project_id = await KnowledgeTransferManager.get_project_id(self.context)
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

        # Create the information request using KnowledgeTransferManager
        success, request = await KnowledgeTransferManager.create_information_request(
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
        project_id = await KnowledgeTransferManager.get_project_id(self.context)
        if not project_id:
            logger.warning("No project ID found for this conversation")
            return "No project associated with this conversation. Unable to delete information request."

        try:
            cleaned_request_id = request_id.strip()
            cleaned_request_id = cleaned_request_id.replace('"', "").replace("'", "")

            # Read the information request
            information_request = ProjectStorage.read_information_request(project_id, cleaned_request_id)

            if not information_request:
                # Try to find it in all requests with improved matching algorithm
                all_requests = ProjectStorage.get_all_information_requests(project_id)
                matching_request = None

                available_ids = [req.request_id for req in all_requests if req.conversation_id == str(self.context.id)]

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
                        logger.debug(f"Reformatted ID without hyphens to: {formatted_id}")
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
                        break

                if matching_request:
                    information_request = matching_request
                    request_id = matching_request.request_id
                else:
                    logger.warning(
                        f"Failed deletion attempt - request ID '{request_id}' not found in project {project_id}"
                    )
                    if available_ids:
                        id_examples = ", ".join([f"`{id[:8]}...`" for id in available_ids[:3]])
                        return f"Information request with ID '{request_id}' not found. Your available requests have IDs like: {id_examples}. Please check and try again with the exact ID."
                    else:
                        return f"Information request with ID '{request_id}' not found. You don't have any active requests to delete."

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
                        role_data = read_model(role_file, ConversationKnowledgePackageManager.ConversationRoleInfo)
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

    async def add_project_goal(self, goal_name: str, goal_description: str, learning_outcomes: List[str]) -> str:
        """
        Add a learning objective to the knowledge brief with measurable learning outcomes.

        Learning objectives should define what knowledge areas learners need to understand.
        Each objective must have clear, measurable learning outcomes that learners can mark as achieved.

        WHEN TO USE:
        - When defining what knowledge areas team members need to understand
        - When breaking down knowledge requirements into specific, learnable objectives
        - After creating a knowledge brief, before marking the transfer ready for learning
        - When users ask to add or define learning objectives or knowledge areas

        Args:
            goal_name: A concise, clear name for the learning objective (e.g., "Understanding User Authentication")
            goal_description: A detailed description explaining what knowledge needs to be understood
            learning_outcomes: List of specific, measurable outcomes that indicate when the objective is achieved
                             (e.g., ["Can explain authentication flow", "Can implement password security"])

        Returns:
            A message indicating success or failure
        """

        if self.role is not ConversationRole.COORDINATOR:
            return "Only Coordinator can add learning objectives."

        # Get project ID
        project_id = await KnowledgeTransferManager.get_project_id(self.context)
        if not project_id:
            return "No project associated with this conversation. Please create a project brief first."

        # Get existing project brief
        brief = await KnowledgeTransferManager.get_project_brief(self.context)
        if not brief:
            return "No project brief found. Please create one first with create_project_brief."

        # Use the formatted command processor from chat.py to leverage existing functionality
        criteria_str = ""
        if len(learning_outcomes) > 0:
            criteria_str = "|" + ";".join(learning_outcomes)

        command_content = f"/add-goal {goal_name}|{goal_description}{criteria_str}"

        return await invoke_command_handler(
            context=self.context,
            command_content=command_content,
            handler_func=handle_add_goal_command,
            success_message=f"Learning objective '{goal_name}' added to knowledge brief successfully.",
            error_prefix="Error adding learning objective",
        )

    async def delete_project_goal(self, goal_index: int) -> str:
        """
        Delete a learning objective from the knowledge package by index.

        WHEN TO USE:
        - When a user explicitly requests to remove or delete a specific learning objective
        - When objectives need to be reorganized and redundant/obsolete objectives removed
        - When an objective was added by mistake or is no longer relevant to the knowledge transfer
        - Only before marking the knowledge package as ready for transfer

        NOTE: This action is irreversible and will remove all learning outcomes associated with the objective.
        First use get_project_info() to see the list of objectives and their indices before deletion.

        Args:
            goal_index: The index of the learning objective to delete (0-based integer). Use get_project_info() first to see the
                       correct indices of objectives. For example, to delete the first objective, use goal_index=0.

        Returns:
            A message indicating success or failure
        """

        if self.role is not ConversationRole.COORDINATOR:
            return "Only Coordinator can delete learning objectives."

        # Get project ID - validate knowledge package exists
        project_id = await KnowledgeTransferManager.get_project_id(self.context)
        if not project_id:
            return "No knowledge package associated with this conversation."

        # Call the KnowledgeTransferManager method to delete the learning objective
        success, result = await KnowledgeTransferManager.delete_project_goal(
            context=self.context,
            goal_index=goal_index,
        )

        if success:
            # Notify the user about the successful deletion
            await self.context.send_messages(
                NewConversationMessage(
                    content=f"Learning objective '{result}' has been successfully deleted from the knowledge package.",
                    message_type=MessageType.notice,
                )
            )
            return f"Learning objective '{result}' has been successfully deleted from the knowledge package."
        else:
            # Return the error message
            return f"Error deleting goal: {result}"

    async def mark_criterion_completed(self, goal_index: int, criterion_index: int) -> str:
        """
        Mark a success criterion as completed for tracking project progress.

        WHEN TO USE:
        - When the user reports completing a specific task or deliverable
        - When evidence has been provided that a success criterion has been met
        - When a milestone for one of the project goals has been achieved
        - When tracking progress and updating the project status

        Each completed criterion moves the project closer to completion. When all criteria
        are completed, the project can be marked as complete.

        IMPORTANT: Always use get_project_info() first to see the current goals, criteria, and their indices
        before marking anything as complete.

        Args:
            goal_index: The index of the goal (0-based integer) from get_project_info() output
            criterion_index: The index of the criterion within the goal (0-based integer)

        Returns:
            A message indicating success or failure
        """

        if self.role is not ConversationRole.TEAM:
            return "Only Team members can mark criteria as completed."

        # Get project ID
        project_id = await KnowledgeTransferManager.get_project_id(self.context)
        if not project_id:
            return "No project associated with this conversation. Unable to mark criterion as completed."

        # Get existing project brief
        brief = await KnowledgeTransferManager.get_project_brief(self.context)
        if not brief:
            return "No project brief found."

        # Using 0-based indexing directly, no adjustment needed

        # Get the project to access goals
        project = ProjectStorage.read_project(project_id)
        if not project or not project.learning_objectives:
            return "No project goals found."

        # Validate indices
        if goal_index < 0 or goal_index >= len(project.learning_objectives):
            return f"Invalid goal index {goal_index}. Valid indexes are 0 to {len(project.learning_objectives) - 1}. There are {len(project.learning_objectives)} goals."

        goal = project.learning_objectives[goal_index]

        if criterion_index < 0 or criterion_index >= len(goal.learning_outcomes):
            return f"Invalid criterion index {criterion_index}. Valid indexes for goal '{goal.name}' are 0 to {len(goal.learning_outcomes) - 1}. Goal '{goal.name}' has {len(goal.learning_outcomes)} criteria."

        # Update the criterion
        criterion = goal.learning_outcomes[criterion_index]

        if criterion.achieved:
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
        criterion.achieved = True
        criterion.achieved_at = datetime.utcnow()
        criterion.achieved_by = current_user_id

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
            if project and project.learning_objectives:
                for g in project.learning_objectives:
                    total_criteria += len(g.learning_outcomes)
                    completed_criteria += sum(1 for c in g.learning_outcomes if c.achieved)

            # Update project info with criteria stats
            # Note: completed_criteria and total_criteria not in KnowledgePackageInfo model

            # Calculate progress percentage
            if total_criteria > 0:
                project_info.completion_percentage = int((completed_criteria / total_criteria) * 100)

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
            if project and project.learning_objectives:
                for g in project.learning_objectives:
                    total += len(g.learning_outcomes)
                    completed += sum(1 for c in g.learning_outcomes if c.achieved)

            if completed == total and total > 0:
                # Automatically complete the project
                success, project_info = await KnowledgeTransferManager.complete_project(
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

        return f"Learning outcome '{criterion.description}' for objective '{goal.name}' marked as achieved."

    async def mark_project_ready_for_working(self) -> str:
        """
        Mark the knowledge package as ready for transfer.
        This is a milestone function that transitions from Organizing to Ready for Transfer state.

        Returns:
            A message indicating success or failure
        """

        if self.role is not ConversationRole.COORDINATOR:
            return "Only Coordinator can mark a knowledge package as ready for transfer."

        # Get project ID
        project_id = await KnowledgeTransferManager.get_project_id(self.context)
        if not project_id:
            return "No knowledge package associated with this conversation. Unable to mark package as ready for transfer."

        # Get existing knowledge brief, digest, and package
        brief = ProjectStorage.read_project_brief(project_id)
        whiteboard = ProjectStorage.read_project_whiteboard(project_id)
        project = ProjectStorage.read_project(project_id)

        if not brief:
            return "No knowledge brief found. Please create one before marking as ready for transfer."

        if not project or not project.learning_objectives:
            return "Knowledge package has no learning objectives. Please add at least one objective before marking as ready for transfer."

        # Check if at least one objective has learning outcomes
        has_criteria = False
        for goal in project.learning_objectives:
            if goal.learning_outcomes:
                has_criteria = True
                break

        if not has_criteria:
            return "No learning outcomes defined. Please add at least one learning outcome to an objective before marking as ready for transfer."

        # Check if digest has content
        if not whiteboard or not whiteboard.content:
            return "Knowledge digest is empty. Content will be automatically generated as the transfer progresses."

        # Get or create knowledge package info
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
            # Create new knowledge package info if it doesn't exist
            project_info = KnowledgePackageInfo(
                package_id=project_id,
                coordinator_conversation_id=str(self.context.id),
                transfer_state=KnowledgeTransferState.ORGANIZING,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

        # Update state to ready_for_transfer
        if isinstance(project_info, dict):
            # Handle the dict case for backward compatibility
            project_info["transfer_state"] = KnowledgeTransferState.READY_FOR_TRANSFER
            project_info["transfer_notes"] = "Knowledge package is now ready for transfer"
            project_info["updated_at"] = datetime.utcnow()
        else:
            # Handle the KnowledgePackageInfo case
            project_info.transfer_state = KnowledgeTransferState.READY_FOR_TRANSFER
            project_info.transfer_notes = "Knowledge package is now ready for transfer"
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
                content="🎯 Knowledge package has been marked as READY FOR TRANSFER. Team members have been notified and can now begin learning.",
                message_type=MessageType.chat,
            )
        )

        return "Knowledge package successfully marked as ready for transfer."

    async def report_project_completion(self) -> str:
        """
        Report that the knowledge transfer is complete, concluding the transfer lifecycle.

        WHEN TO USE:
        - When all learning outcomes for all objectives have been marked as achieved
        - When the user confirms the knowledge has been successfully learned
        - When the learning objectives have been fully achieved
        - When it's time to formally conclude the knowledge transfer

        This is a significant milestone that indicates the knowledge transfer has successfully
        achieved all its learning objectives. Before using this tool, verify that all learning outcomes
        have been marked as achieved using get_project_info().

        Returns:
            A message indicating success or failure
        """

        if self.role is not ConversationRole.TEAM:
            return "Only Team members can report knowledge transfer completion."

        # Get project ID
        project_id = await KnowledgeTransferManager.get_project_id(self.context)
        if not project_id:
            return "No knowledge package associated with this conversation. Unable to report transfer completion."

        # Get existing knowledge package info
        project_info = ProjectStorage.read_project_info(project_id)
        if not project_info:
            return "No knowledge package information found. Cannot complete transfer without package information."

        # Check if all outcomes are achieved
        if getattr(project_info, "achieved_outcomes", 0) < getattr(project_info, "total_outcomes", 0):
            # Note: total_outcomes and achieved_outcomes are in KnowledgePackageInfo model
            remaining = getattr(project_info, "total_outcomes", 0) - getattr(project_info, "achieved_outcomes", 0)
            return f"Cannot complete knowledge transfer - {remaining} learning outcomes are still pending achievement."

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
        project_info.transfer_state = KnowledgeTransferState.COMPLETED
        project_info.completion_percentage = 100
        project_info.transfer_notes = "Project is now complete"

        # Add lifecycle metadata
        # Note: lifecycle field doesn't exist in KnowledgePackageInfo

        # Lifecycle tracking would need to be implemented elsewhere

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

    async def suggest_next_action(self) -> Dict[str, Any]:
        """
        Suggest the next action the user should take based on project state.

        Returns:
            Dict with suggestion details
        """
        # Get project ID
        project_id = await KnowledgeTransferManager.get_project_id(self.context)
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
                    "parameters": {"name": "", "description": ""},
                }
            else:
                return {
                    "suggestion": "wait_for_coordinator",
                    "reason": "No project brief found. The Coordinator needs to create one before you can proceed.",
                    "priority": "medium",
                    "function": None,
                }

        # Check if goals exist
        if not project or not project.learning_objectives:
            if self.role is ConversationRole.COORDINATOR:
                return {
                    "suggestion": "add_project_goal",
                    "reason": "Project has no goals. Add at least one goal with success criteria.",
                    "priority": "high",
                    "function": "add_project_goal",
                    "parameters": {"goal_name": "", "goal_description": "", "learning_outcomes": []},
                }
            else:
                return {
                    "suggestion": "wait_for_goals",
                    "reason": "Project has no goals. The Coordinator needs to add goals before you can proceed.",
                    "priority": "medium",
                    "function": None,
                }

        # Check project info if project is ready for working
        ready_for_working = project_info.transfer_state == KnowledgeTransferState.READY_FOR_TRANSFER

        if not ready_for_working and self.role is ConversationRole.COORDINATOR:
            # Check if it's ready to mark as ready for working
            has_goals = bool(project and project.learning_objectives)
            has_criteria = bool(
                project
                and project.learning_objectives
                and any(bool(goal.learning_outcomes) for goal in project.learning_objectives)
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
        criteria = await KnowledgeTransferManager.get_project_criteria(self.context)
        incomplete_criteria = [criterion for criterion in criteria if not criterion.achieved]

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
            if project and project.learning_objectives:
                # Find the first uncompleted criterion
                for goal_index, goal in enumerate(project.learning_objectives):
                    for criterion_index, criterion in enumerate(goal.learning_outcomes):
                        if not criterion.achieved:
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
