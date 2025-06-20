"""
Knowledge Transfer Assistant tool functions.

This module defines tool functions for the Knowledge Transfer Assistant that can be used
by the LLM during chat completions to proactively assist users.
"""

from datetime import datetime
from typing import Callable, List, Literal
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
    handle_add_learning_objective_command,
)
from .conversation_clients import ConversationClientManager
from .conversation_share_link import ConversationKnowledgePackageManager
from .data import (
    LearningOutcomeAchievement,
    LogEntryType,
    RequestPriority,
)
from .logging import logger
from .manager import KnowledgeTransferManager
from .notifications import ProjectNotifier
from .storage import ShareStorage, ShareStorageManager
from .storage_models import ConversationRole
from .utils import require_current_user


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


class ShareTools:
    """Tools for the Knowledge Transfer Assistant to use during chat completions."""

    def __init__(self, context: ConversationContext, role: ConversationRole):
        """
        Initialize the knowledge transfer tools with the current conversation context.

        Args:
            context: The conversation context
            role: The assistant's role (ConversationRole enum)
        """
        self.context = context
        self.role = role
        self.tool_functions = ToolFunctions()

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

            self.tool_functions.add_function(
                self.update_audience,
                "update_audience",
                "Update the target audience description for this knowledge package",
            )

            self.tool_functions.add_function(
                self.add_learning_objective,
                "add_learning_objective",
                "Add a learning objective to the knowledge brief with measurable learning outcomes",
            )
            self.tool_functions.add_function(
                self.update_learning_objective,
                "update_learning_objective",
                "Update an existing learning objective's name, description, or learning outcomes",
            )
            self.tool_functions.add_function(
                self.delete_learning_objective,
                "delete_learning_objective",
                "Delete a learning objective from the knowledge package by index",
            )
            self.tool_functions.add_function(
                self.set_learning_intention,
                "set_learning_intention",
                "Set or update whether this knowledge package is intended for specific learning outcomes or general exploration",
            )

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
            self.tool_functions.add_function(
                self.report_transfer_completion,
                "report_transfer_completion",
                "Report that the knowledge transfer is complete",
            )
            self.tool_functions.add_function(
                self.mark_learning_outcome_achieved,
                "mark_learning_outcome_achieved",
                "Mark a learning outcome as achieved",
            )

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
            return "Only Coordinator can create knowledge briefs."

        # First, make sure we have a knowledge package associated with this conversation
        share_id = await KnowledgeTransferManager.get_share_id(self.context)
        if not share_id:
            return "No knowledge package associated with this conversation. Please create a knowledge package first."

        # Create a new knowledge brief using KnowledgeTransferManager
        brief = await KnowledgeTransferManager.update_knowledge_brief(
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

        # Get share ID
        share_id = await KnowledgeTransferManager.get_share_id(self.context)
        if not share_id:
            return "No knowledge package associated with this conversation. Unable to resolve information request."

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
        - When encountering a blocker that prevents progress on a learning objective
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

        # Get share ID
        share_id = await KnowledgeTransferManager.get_share_id(self.context)
        if not share_id:
            return "No knowledge package associated with this conversation. Unable to create information request."

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

        # Get share ID
        share_id = await KnowledgeTransferManager.get_share_id(self.context)
        if not share_id:
            logger.warning("No share ID found for this conversation")
            return "No knowledge package associated with this conversation. Unable to delete information request."

        try:
            cleaned_request_id = request_id.strip()
            cleaned_request_id = cleaned_request_id.replace('"', "").replace("'", "")

            # Read the information request
            information_request = ShareStorage.read_information_request(share_id, cleaned_request_id)

            if not information_request:
                # Try to find it in all requests with improved matching algorithm
                all_requests = ShareStorage.get_all_information_requests(share_id)
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
                        f"Failed deletion attempt - request ID '{request_id}' not found in project {share_id}"
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
            await ShareStorage.log_share_event(
                context=self.context,
                share_id=share_id,
                entry_type=LogEntryType.REQUEST_DELETED.value,
                message=f"Information request '{request_title}' was deleted by {current_username}",
                related_entity_id=actual_request_id,
                metadata={
                    "request_title": request_title,
                    "deleted_by": current_user_id,
                    "deleted_by_name": current_username,
                },
            )

            # Delete the information request from the main share data
            package = ShareStorage.read_share(share_id)
            if package and package.requests:
                # Remove the request from the list
                package.requests = [req for req in package.requests if req.request_id != actual_request_id]
                # Save the updated package
                ShareStorage.write_share(share_id, package)

            # Notify Coordinator about the deletion
            try:
                # Get Coordinator conversation ID

                coordinator_dir = ShareStorageManager.get_share_dir(share_id) / ConversationRole.COORDINATOR.value
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
            await ShareStorage.refresh_all_share_uis(self.context, share_id)

            return f"Information request '{request_title}' has been successfully deleted."

        except Exception as e:
            logger.exception(f"Error deleting information request: {e}")
            return f"Error deleting information request: {str(e)}. Please try again later."

    async def add_learning_objective(self, objective_name: str, description: str, learning_outcomes: List[str]) -> str:
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
            objective_name: A concise, clear name for the learning objective (e.g., "Understanding User Authentication")
            description: A detailed description explaining what knowledge needs to be understood
            learning_outcomes: List of specific, measurable outcomes that indicate when the objective is achieved
                             (e.g., ["Can explain authentication flow", "Can implement password security"])

        Returns:
            A message indicating success or failure
        """

        if self.role is not ConversationRole.COORDINATOR:
            return "Only Coordinator can add learning objectives."

        # Get share ID
        share_id = await KnowledgeTransferManager.get_share_id(self.context)
        if not share_id:
            return "No knowledge package associated with this conversation. Please create a knowledge brief first."

        # Get existing knowledge brief
        brief = await KnowledgeTransferManager.get_knowledge_brief(self.context)
        if not brief:
            return "No knowledge brief found. Please create one first with update_brief."

        # Use the formatted command processor from chat.py to leverage existing functionality
        criteria_str = ""
        if len(learning_outcomes) > 0:
            criteria_str = "|" + ";".join(learning_outcomes)

        command_content = f"/add-learning-objective {objective_name}|{description}{criteria_str}"

        return await invoke_command_handler(
            context=self.context,
            command_content=command_content,
            handler_func=handle_add_learning_objective_command,
            success_message=f"Learning objective '{objective_name}' added to knowledge brief successfully.",
            error_prefix="Error adding learning objective",
        )

    async def update_learning_objective(
        self,
        objective_index: int,
        objective_name: str,
        description: str,
        learning_outcomes: List[str],
    ) -> str:
        """
        Update an existing learning objective's name, description, or learning outcomes.

        WHEN TO USE:
        - When refining the scope or clarity of an existing learning objective
        - When adding, removing, or modifying learning outcomes for an objective
        - When updating the description to better reflect the knowledge area
        - When reorganizing objectives to improve knowledge transfer structure

        Args:
            objective_index: The index of the learning objective to update (0-based integer)
            objective_name: New name for the objective (empty string to keep current name)
            description: New description (empty string to keep current description)
            learning_outcomes: New list of learning outcomes (empty list to keep current outcomes)

        Returns:
            A message indicating success or failure
        """
        if self.role is not ConversationRole.COORDINATOR:
            return "Only Coordinator can update learning objectives."

        # Get share ID
        share_id = await KnowledgeTransferManager.get_share_id(self.context)
        if not share_id:
            return "No knowledge package associated with this conversation. Please create a knowledge brief first."

        # Get existing knowledge package
        knowledge_package = ShareStorage.read_share(share_id)
        if not knowledge_package or not knowledge_package.learning_objectives:
            return "No learning objectives found. Please add objectives before updating them."

        # Validate index
        if objective_index < 0 or objective_index >= len(knowledge_package.learning_objectives):
            return f"Invalid objective index {objective_index}. Valid indexes are 0 to {len(knowledge_package.learning_objectives) - 1}. There are {len(knowledge_package.learning_objectives)} objectives."

        # Get the objective to update
        objective = knowledge_package.learning_objectives[objective_index]
        original_name = objective.name

        # Update fields if provided (empty string/list means no change)
        if objective_name.strip():
            objective.name = objective_name.strip()

        if description.strip():
            objective.description = description.strip()

        if learning_outcomes:
            # Convert learning outcomes to LearningOutcome objects
            from .data import LearningOutcome

            objective.learning_outcomes = [
                LearningOutcome(description=outcome.strip()) for outcome in learning_outcomes if outcome.strip()
            ]

        # Get user information for logging
        current_user_id = await require_current_user(self.context, "update learning objective")
        if not current_user_id:
            return "Could not identify current user."

        # Save the updated knowledge package
        ShareStorage.write_share(share_id, knowledge_package)

        # Log the objective update
        changes_made = []
        if objective_name.strip():
            changes_made.append(f"name: '{original_name}' → '{objective_name.strip()}'")
        if description.strip():
            changes_made.append("description updated")
        if learning_outcomes:
            filtered_outcomes = [o for o in learning_outcomes if o.strip()]
            changes_made.append(f"learning outcomes updated ({len(filtered_outcomes)} outcomes)")

        changes_text = ", ".join(changes_made) if changes_made else "no changes specified"

        await ShareStorage.log_share_event(
            context=self.context,
            share_id=share_id,
            entry_type=LogEntryType.LEARNING_OBJECTIVE_UPDATED.value,
            message=f"Updated learning objective '{objective.name}': {changes_text}",
            metadata={
                "objective_index": objective_index,
                "objective_name": objective.name,
                "changes": changes_text,
            },
        )

        # Notify linked conversations
        await ProjectNotifier.notify_project_update(
            context=self.context,
            share_id=share_id,
            update_type="learning_objective",
            message=f"Learning objective '{objective.name}' has been updated",
        )

        # Update all share UI inspectors
        await ShareStorage.refresh_all_share_uis(self.context, share_id)

        # Send notification to current conversation
        await self.context.send_messages(
            NewConversationMessage(
                content=f"Learning objective '{objective.name}' has been successfully updated: {changes_text}.",
                message_type=MessageType.notice,
            )
        )

        return f"Learning objective '{objective.name}' has been successfully updated: {changes_text}."

    async def delete_learning_objective(self, objective_index: int) -> str:
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
            objective_index: The index of the learning objective to delete (0-based integer). Use get_project_info() first to see the
                       correct indices of objectives. For example, to delete the first objective, use objective_index=0.

        Returns:
            A message indicating success or failure
        """

        if self.role is not ConversationRole.COORDINATOR:
            return "Only Coordinator can delete learning objectives."

        # Get project ID - validate knowledge package exists
        share_id = await KnowledgeTransferManager.get_share_id(self.context)
        if not share_id:
            return "No knowledge package associated with this conversation."

        # Call the KnowledgeTransferManager method to delete the learning objective
        success, result = await KnowledgeTransferManager.delete_learning_objective(
            context=self.context,
            objective_index=objective_index,
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
            return f"Error deleting learning objective: {result}"

    async def mark_learning_outcome_achieved(self, objective_index: int, criterion_index: int) -> str:
        """
        Mark a learning outcome as achieved for tracking knowledge transfer progress.

        WHEN TO USE:
        - When the user reports completing a specific learning task or deliverable
        - When evidence has been provided that a learning outcome has been met
        - When a milestone for one of the learning objectives has been achieved
        - When tracking progress and updating the transfer status

        Each completed outcome moves the knowledge transfer closer to completion. When all outcomes
        are achieved, the transfer can be marked as complete.

        IMPORTANT: Always use get_share_info() first to see the current objectives, outcomes, and their indices
        before marking anything as complete.

        Args:
            objective_index: The index of the objective (0-based integer) from get_share_info() output
            criterion_index: The index of the outcome within the objective (0-based integer)

        Returns:
            A message indicating success or failure
        """

        if self.role is not ConversationRole.TEAM:
            return "Only Team members can mark criteria as completed."

        # Get share ID
        share_id = await KnowledgeTransferManager.get_share_id(self.context)
        if not share_id:
            return "No knowledge package associated with this conversation. Unable to mark outcome as achieved."

        # Get existing knowledge brief
        brief = await KnowledgeTransferManager.get_knowledge_brief(self.context)
        if not brief:
            return "No knowledge brief found."

        # Using 0-based indexing directly, no adjustment needed

        # Get the knowledge package to access objectives
        knowledge_package = ShareStorage.read_share(share_id)
        if not knowledge_package or not knowledge_package.learning_objectives:
            return "No learning objectives found."

        # Validate indices
        if objective_index < 0 or objective_index >= len(knowledge_package.learning_objectives):
            return f"Invalid objective index {objective_index}. Valid indexes are 0 to {len(knowledge_package.learning_objectives) - 1}. There are {len(knowledge_package.learning_objectives)} objectives."

        objective = knowledge_package.learning_objectives[objective_index]

        if criterion_index < 0 or criterion_index >= len(objective.learning_outcomes):
            return f"Invalid outcome index {criterion_index}. Valid indexes for objective '{objective.name}' are 0 to {len(objective.learning_outcomes) - 1}. Objective '{objective.name}' has {len(objective.learning_outcomes)} outcomes."

        # Update the outcome
        outcome = objective.learning_outcomes[criterion_index]
        conversation_id = str(self.context.id)

        # Check if already achieved by this conversation
        if knowledge_package.is_outcome_achieved_by_conversation(outcome.id, conversation_id):
            return f"Outcome '{outcome.description}' is already marked as achieved by this team member."

        # Get current user information
        participants = await self.context.get_participants()
        current_user_id = None

        for participant in participants.participants:
            if participant.role == "user":
                current_user_id = participant.id
                break

        if not current_user_id:
            return "Could not identify current user."

        # Ensure team conversation info exists
        if conversation_id not in knowledge_package.team_conversations:
            return "Team conversation not properly registered. Please contact the coordinator."

        # Create achievement record
        achievement = LearningOutcomeAchievement(outcome_id=outcome.id, achieved=True, achieved_at=datetime.utcnow())

        # Add achievement to team conversation's achievements
        knowledge_package.team_conversations[conversation_id].outcome_achievements.append(achievement)

        # Update team conversation's last active timestamp
        knowledge_package.team_conversations[conversation_id].last_active_at = datetime.utcnow()

        # Save the updated knowledge package with the achieved outcome
        ShareStorage.write_share(share_id, knowledge_package)

        # Log the outcome achievement
        await ShareStorage.log_share_event(
            context=self.context,
            share_id=share_id,
            entry_type=LogEntryType.OUTCOME_ATTAINED.value,
            message=f"Learning outcome achieved: {outcome.description}",
            related_entity_id=None,
            metadata={"objective_name": objective.name, "outcome_description": outcome.description},
        )

        # Update knowledge package
        knowledge_package = ShareStorage.read_share(share_id)

        if knowledge_package:
            # Get overall completion statistics
            achieved_outcomes, total_outcomes = knowledge_package.get_overall_completion()

            # Update knowledge package with outcome stats
            knowledge_package.achieved_outcomes = achieved_outcomes
            knowledge_package.total_outcomes = total_outcomes

            # Calculate progress percentage
            if total_outcomes > 0:
                knowledge_package.completion_percentage = int((achieved_outcomes / total_outcomes) * 100)

            # Update metadata
            knowledge_package.updated_at = datetime.utcnow()
            knowledge_package.updated_by = current_user_id
            knowledge_package.version += 1

            # Save the updated knowledge package
            ShareStorage.write_share(share_id, knowledge_package)

            # Notify linked conversations with a message
            await ProjectNotifier.notify_project_update(
                context=self.context,
                share_id=share_id,
                update_type="share_info",
                message=f"Learning outcome '{outcome.description}' for objective '{objective.name}' has been marked as achieved.",
            )

            # Update all share UI inspectors
            await ShareStorage.refresh_all_share_uis(self.context, share_id)

            # Check if all outcomes are achieved for transfer completion
            # Get the knowledge package to check completion status
            knowledge_package = ShareStorage.read_share(share_id)
            if knowledge_package and knowledge_package._is_transfer_complete():
                # Automatically complete the transfer
                success, share_info = await KnowledgeTransferManager.complete_project(
                    context=self.context,
                    summary=f"All {total_outcomes} learning outcomes have been achieved! Knowledge transfer has been automatically marked as complete.",
                )

                if success:
                    await self.context.send_messages(
                        NewConversationMessage(
                            content="🎉 All learning outcomes have been achieved! The knowledge transfer has been automatically marked as complete.",
                            message_type=MessageType.notice,
                        )
                    )
                else:
                    await self.context.send_messages(
                        NewConversationMessage(
                            content="🎉 All learning outcomes have been achieved! Would you like me to formally complete the knowledge transfer?",
                            message_type=MessageType.notice,
                        )
                    )

        await self.context.send_messages(
            NewConversationMessage(
                content=f"Learning outcome '{outcome.description}' for objective '{objective.name}' has been marked as achieved.",
                message_type=MessageType.notice,
            )
        )

        return f"Learning outcome '{outcome.description}' for objective '{objective.name}' marked as achieved."

    async def set_learning_intention(self, is_for_specific_outcomes: bool) -> str:
        """
        Set or update whether this knowledge package is intended for specific learning outcomes or general exploration.

        When is_for_specific_outcomes is True, the package will require learning objectives with outcomes.
        When is_for_specific_outcomes is False, the package is for general knowledge exploration.

        Args:
            is_for_specific_outcomes: True if this package should have learning objectives and outcomes,
                                    False if this is for general exploration

        Returns:
            A message indicating success or failure
        """
        if self.role is not ConversationRole.COORDINATOR:
            return "Only Coordinator can set learning intention."

        # Get share ID
        share_id = await KnowledgeTransferManager.get_share_id(self.context)
        if not share_id:
            return "No knowledge package associated with this conversation. Please create a knowledge brief first."

        # Get existing knowledge package
        package = ShareStorage.read_share(share_id)
        if not package:
            return "No knowledge package found. Please create a knowledge brief first."

        # Update the intention
        package.is_intended_to_accomplish_outcomes = is_for_specific_outcomes
        package.updated_at = datetime.utcnow()

        # Save the updated package
        ShareStorage.write_share(share_id, package)

        # Provide appropriate guidance based on the choice
        if is_for_specific_outcomes:
            guidance = "This knowledge package is now set for specific learning outcomes. You'll need to add learning objectives with measurable outcomes."
        else:
            guidance = "This knowledge package is now set for general exploration. No specific learning objectives are required."

        return f"Learning intention updated successfully. {guidance}"

    async def update_audience(self, audience_description: str) -> str:
        """
        Update the target audience description for this knowledge package.

        Args:
            audience_description: Description of the intended audience and their existing knowledge level

        Returns:
            A message indicating success or failure
        """
        if self.role is not ConversationRole.COORDINATOR:
            return "Only Coordinator can update the audience description."

        # Get share ID
        share_id = await KnowledgeTransferManager.get_share_id(self.context)
        if not share_id:
            return "No knowledge package associated with this conversation. Please create a knowledge brief first."

        # Get existing knowledge package
        package = ShareStorage.read_share(share_id)
        if not package:
            return "No knowledge package found. Please create a knowledge brief first."

        # Update the audience
        package.audience = audience_description.strip()
        package.updated_at = datetime.utcnow()

        # Save the updated package
        ShareStorage.write_share(share_id, package)

        return f"Target audience updated successfully: {audience_description}"

    async def report_transfer_completion(self) -> str:
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
        share_id = await KnowledgeTransferManager.get_share_id(self.context)
        if not share_id:
            return "No knowledge package associated with this conversation. Unable to report transfer completion."

        # Get existing knowledge package
        package = ShareStorage.read_share(share_id)
        if not package:
            return "No knowledge package found. Cannot complete transfer without package information."

        # Check if all outcomes are achieved
        if package.achieved_outcomes < package.total_outcomes:
            remaining = package.total_outcomes - package.achieved_outcomes
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

        # Update knowledge package to completed
        package.completion_percentage = 100
        package.transfer_notes = "Project is now complete"

        # Update metadata
        package.updated_at = datetime.utcnow()
        package.updated_by = current_user_id
        package.version += 1

        # Save the updated knowledge package
        ShareStorage.write_share(share_id, package)

        # Log the milestone transition
        await ShareStorage.log_share_event(
            context=self.context,
            share_id=share_id,
            entry_type=LogEntryType.SHARE_COMPLETED.value,
            message="Project marked as COMPLETED",
            metadata={"milestone": "project_completed"},
        )

        # Notify linked conversations with a message
        await ProjectNotifier.notify_project_update(
            context=self.context,
            share_id=share_id,
            update_type="project_completed",
            message="🎉 **Project Complete**: Team has reported that all project objectives have been achieved. The project is now complete.",
        )

        # Update all project UI inspectors
        await ShareStorage.refresh_all_share_uis(self.context, share_id)

        await self.context.send_messages(
            NewConversationMessage(
                content="🎉 **Project Complete**: All objectives have been achieved and the project is now complete. The Coordinator has been notified.",
                message_type=MessageType.chat,
            )
        )

        return "Knowledge transfer successfully marked as complete. All participants have been notified."
