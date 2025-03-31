"""
Mission Assistant tool functions.

This module defines tool functions for the Mission Assistant that can be used
by the LLM during chat completions to proactively assist users.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
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

from .command_processor import (
    handle_add_goal_command,
    handle_add_kb_section_command,
)
from .mission_data import (
    LogEntryType,
    MissionState,
    MissionStatus,
    RequestPriority,
    RequestStatus,
)
from .mission_manager import MissionManager, MissionRole
from .mission_storage import (
    MissionStorage,
    ConversationMissionManager,
    MissionNotifier,
)

logger = logging.getLogger(__name__)


class MissionTools:
    """Tools for the Mission Assistant to use during chat completions."""

    def __init__(self, context: ConversationContext, role: str):
        """
        Initialize the mission tools with the current conversation context.

        Args:
            context: The conversation context
            role: The assistant's role ("hq" or "field")
        """
        self.context = context
        self.role = role
        self.tool_functions = ToolFunctions()

        # Register common tools for both roles
        self.tool_functions.add_function(
            self.get_mission_info, "get_mission_info", "Get information about the current mission state"
        )

        # Register role-specific tools
        if role == "hq":
            # HQ-specific tools
            self.tool_functions.add_function(
                self.create_mission_briefing,
                "create_mission_briefing",
                "Create a mission briefing with a name and description",
            )
            self.tool_functions.add_function(
                self.add_mission_goal,
                "add_mission_goal",
                "Add a goal to the mission briefing with optional success criteria",
            )
            self.tool_functions.add_function(
                self.add_kb_section, "add_kb_section", "Add a section to the mission knowledge base"
            )
            self.tool_functions.add_function(
                self.resolve_field_request, "resolve_field_request", "Resolve a field request with information"
            )
            self.tool_functions.add_function(
                self.mark_mission_ready_for_field,
                "mark_mission_ready_for_field",
                "Mark the mission as ready for field operations",
            )
        else:
            # Field-specific tools
            self.tool_functions.add_function(
                self.create_field_request,
                "create_field_request",
                "Create a field request for information or to report a blocker",
            )
            self.tool_functions.add_function(
                self.update_mission_status, "update_mission_status", "Update the status and progress of the mission"
            )
            self.tool_functions.add_function(
                self.mark_criterion_completed, "mark_criterion_completed", "Mark a success criterion as completed"
            )
            self.tool_functions.add_function(
                self.report_mission_completion, "report_mission_completion", "Report that the mission is complete"
            )
            self.tool_functions.add_function(
                self.detect_field_request_needs,
                "detect_field_request_needs",
                "Analyze user message to detect potential field request needs",
            )

        # Common detection tool for both roles
        self.tool_functions.add_function(
            self.suggest_next_action,
            "suggest_next_action",
            "Suggest the next action the user should take based on mission state",
        )

    async def get_mission_info(self, info_type: Literal["all", "briefing", "kb", "status", "requests"]) -> str:
        """
        Get information about the current mission.

        Args:
            info_type: Type of information to retrieve. Must be one of: all, briefing, kb, status, requests.

        Returns:
            Information about the mission in a formatted string
        """
        if info_type not in ["all", "briefing", "kb", "status", "requests"]:
            return f"Invalid info_type: {info_type}. Must be one of: all, briefing, kb, status, requests. Use 'all' to get all information types."

        # Get the mission ID for the current conversation
        mission_id = await MissionManager.get_mission_id(self.context)
        if not mission_id:
            return "No mission associated with this conversation. Start by creating a mission briefing."

        output = []

        # Get mission briefing if requested
        if info_type in ["all", "briefing"]:
            briefing = await MissionManager.get_mission_briefing(self.context)

            if briefing:
                # Format briefing information
                output.append(f"## Mission Briefing: {briefing.mission_name}")
                output.append(f"\n{briefing.mission_description}\n")

                if briefing.goals:
                    output.append("\n### Goals:\n")

                    for i, goal in enumerate(briefing.goals):
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
                    output.append("\n*No goals defined yet.*")

        # Get mission KB if requested
        if info_type in ["all", "kb"]:
            kb = MissionStorage.read_mission_kb(mission_id)

            if kb and kb.sections:
                output.append("\n## Mission Knowledge Base\n")

                # Sort sections by order
                sorted_sections = sorted(kb.sections.values(), key=lambda s: s.order)

                for section in sorted_sections:
                    output.append(f"### {section.title}")
                    output.append(f"{section.content}")

                    if section.tags:
                        tags = ", ".join(section.tags)
                        output.append(f"\n*Tags: {tags}*")

                    output.append("")
            elif info_type == "kb":
                output.append("\n## Mission Knowledge Base\n")
                output.append("*No knowledge base sections defined yet.*")

        # Get mission status if requested
        if info_type in ["all", "status"]:
            status = MissionStorage.read_mission_status(mission_id)

            if status:
                output.append("\n## Mission Status\n")
                output.append(f"**Current Status**: {status.state.value}")

                if status.progress_percentage is not None:
                    output.append(f"**Overall Progress**: {status.progress_percentage}%")

                if status.status_message:
                    output.append(f"**Status Message**: {status.status_message}")

                if status.completed_criteria > 0:
                    output.append(f"**Success Criteria**: {status.completed_criteria}/{status.total_criteria} complete")

                if status.next_actions:
                    output.append("\n**Next Actions**:")
                    for action in status.next_actions:
                        output.append(f"- {action}")
            elif info_type == "status":
                output.append("\n## Mission Status\n")
                output.append("*No mission status defined yet.*")

        # Get field requests if requested
        if info_type in ["all", "requests"]:
            requests = MissionStorage.get_all_field_requests(mission_id)

            if requests:
                output.append("\n## Field Requests\n")

                # Group requests by status
                active_requests = [r for r in requests if r.status not in [RequestStatus.RESOLVED, RequestStatus.CANCELLED]]
                resolved_requests = [r for r in requests if r.status in [RequestStatus.RESOLVED, RequestStatus.CANCELLED]]

                if active_requests:
                    output.append("### Active Requests")
                    output.append(
                        '\n> 📋 **FOR HQ AGENTS:** To resolve a request, first get the Request ID below, then use `resolve_field_request(request_id="exact-id-here", resolution="your solution")`. Do NOT use the request title as the ID.\n'
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
                output.append("\n## Field Requests\n")
                output.append("*No field requests created yet.*")

        # If no data was found for any category
        if not output:
            return "No mission information found. Start by creating a mission briefing."

        return "\n".join(output)

    async def create_mission_briefing(self, mission_name: str, mission_description: str) -> str:
        """
        Create a mission briefing with a name and description.

        Args:
            mission_name: The name of the mission
            mission_description: A description of the mission

        Returns:
            A message indicating success or failure
        """
        if self.role != "hq":
            return "Only HQ can create mission briefings."

        # First, make sure we have a mission associated with this conversation
        mission_id = await MissionManager.get_mission_id(self.context)
        if not mission_id:
            # Create a new mission if one doesn't exist
            success, new_mission_id = await MissionManager.create_mission(self.context)
            if not success or not new_mission_id:
                return "Failed to create mission. Please try again."
            mission_id = new_mission_id
            
            # Set the conversation role as HQ
            await ConversationMissionManager.set_conversation_role(self.context, mission_id, MissionRole.HQ)

        # Create a new mission briefing using MissionManager
        success, briefing = await MissionManager.create_mission_briefing(
            context=self.context,
            mission_name=mission_name,
            mission_description=mission_description
        )

        if success and briefing:
            await self.context.send_messages(
                NewConversationMessage(
                    content=f"Mission briefing '{mission_name}' created successfully.",
                    message_type=MessageType.notice,
                    metadata={},  # Add empty metadata
                )
            )
            return f"Mission briefing '{mission_name}' created successfully."
        else:
            return "Failed to create mission briefing. Please try again."

    async def add_mission_goal(self, goal_name: str, goal_description: str, success_criteria: List[str]) -> str:
        """
        Add a goal to the mission briefing.

        Args:
            goal_name: The name of the goal
            goal_description: A description of the goal
            success_criteria: Optional list of success criteria. If not provided, an empty list will be used.

        Returns:
            A message indicating success or failure
        """
        if self.role != "hq":
            return "Only HQ can add mission goals."

        # Get mission ID
        mission_id = await MissionManager.get_mission_id(self.context)
        if not mission_id:
            return "No mission associated with this conversation. Please create a mission briefing first."

        # Get existing mission briefing
        briefing = await MissionManager.get_mission_briefing(self.context)
        if not briefing:
            return "No mission briefing found. Please create one first with create_mission_briefing."

        # Use the formatted command processor from chat.py to leverage existing functionality
        criteria_str = ""
        if len(success_criteria) > 0:
            criteria_str = "|" + ";".join(success_criteria)

        command_content = f"/add-goal {goal_name}|{goal_description}{criteria_str}"

        # Create a temporary system message to invoke the command processor
        # This reuses the existing command handling logic from chat.py
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
            await handle_add_goal_command(self.context, temp_message, [])
            return f"Goal '{goal_name}' added to mission briefing successfully."
        except Exception as e:
            logger.exception(f"Error adding goal: {e}")
            return f"Error adding goal: {str(e)}"

    async def add_kb_section(self, title: str, content: str) -> str:
        """
        Add a section to the mission knowledge base.

        Args:
            title: The title of the section
            content: The content of the section

        Returns:
            A message indicating success or failure
        """
        if self.role != "hq":
            return "Only HQ can add knowledge base sections."
            
        # Get mission ID
        mission_id = await MissionManager.get_mission_id(self.context)
        if not mission_id:
            return "No mission associated with this conversation. Please create a mission briefing first."

        # Use the formatted command processor from chat.py to leverage existing functionality
        command_content = f"/add-kb-section {title}|{content}"

        # Create a temporary system message to invoke the KB section command processor
        # This approach maintains consistency with command handling in the chat interface
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
            await handle_add_kb_section_command(self.context, temp_message, [])
            return f"Knowledge base section '{title}' added successfully."
        except Exception as e:
            logger.exception(f"Error adding KB section: {e}")
            return f"Error adding knowledge base section: {str(e)}"

    async def resolve_field_request(self, request_id: str, resolution: str) -> str:
        """
        Resolve a field request with information.

        [HQ ONLY] This tool is only available to HQ agents.

        Args:
            request_id: IMPORTANT! Use the exact Request ID value from get_mission_info output
                       (looks like "012345-abcd-67890"), NOT the title of the request
            resolution: Resolution information to add to the request

        Returns:
            A message indicating success or failure
        """
        if self.role != "hq":
            # Add more detailed error message with guidance
            error_message = (
                "ERROR: Only HQ can resolve field requests. As a Field agent, you should use "
                "create_field_request to send requests to HQ, not try to resolve them yourself. "
                "HQ must use resolve_field_request to respond to your requests."
            )
            logger.warning(f"Field agent attempted to use resolve_field_request: {request_id}")
            return error_message

        # Get mission ID
        mission_id = await MissionManager.get_mission_id(self.context)
        if not mission_id:
            return "No mission associated with this conversation. Unable to resolve field request."

        # Resolve the field request using MissionManager
        success, field_request = await MissionManager.resolve_field_request(
            context=self.context,
            request_id=request_id,
            resolution=resolution
        )

        if success and field_request:
            # Notification is handled by MissionManager.resolve_field_request
            return f"Field request '{field_request.title}' has been resolved."
        else:
            logger.warning(f"Failed to resolve field request. Invalid ID provided: '{request_id}'")
            return f'''ERROR: Could not resolve field request with ID "{request_id}".

IMPORTANT STEPS TO RESOLVE FIELD REQUESTS:
1. FIRST run get_mission_info(info_type="requests") to see the full list of requests
2. Find the request you want to resolve and copy its exact Request ID (looks like "abc123-def-456")
3. Then use resolve_field_request with the EXACT ID from step 2, NOT the title of the request

Example: resolve_field_request(request_id="abc123-def-456", resolution="Your solution here")"'''

    async def create_field_request(
        self, title: str, description: str, priority: Literal["low", "medium", "high", "critical"]
    ) -> str:
        """
        Create a field request to send to HQ for information or to report a blocker.

        This is the MAIN TOOL FOR FIELD AGENTS to request information, documents, or assistance from HQ.
        Field agents should use this tool whenever they need something from HQ.

        Args:
            title: The title of the request (be specific and clear)
            description: A detailed description of what information or help you need from HQ
            priority: The priority of the request. Must be one of: low, medium, high, critical.

        Returns:
            A message indicating success or failure
        """
        if self.role != "field":
            return "Only Field can create field requests."

        # Get mission ID
        mission_id = await MissionManager.get_mission_id(self.context)
        if not mission_id:
            return "No mission associated with this conversation. Unable to create field request."

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

        # Create the field request using MissionManager
        success, request = await MissionManager.create_field_request(
            context=self.context,
            title=title,
            description=description,
            priority=priority_enum
        )

        if success and request:
            await self.context.send_messages(
                NewConversationMessage(
                    content=f"Field request '{title}' created successfully with {priority} priority. HQ has been notified.",
                    message_type=MessageType.notice,
                    metadata={},  # Add empty metadata
                )
            )
            return f"Field request '{title}' created successfully. HQ has been notified."
        else:
            return "Failed to create field request. Please try again."

    async def update_mission_status(
        self,
        status: Literal["planning", "in_progress", "blocked", "completed", "aborted"],
        progress: Optional[int],
        status_message: Optional[str],
        next_actions: Optional[List[str]],
    ) -> str:
        """
        Update the status and progress of the mission.

        Args:
            status: The mission status. Must be one of: planning, in_progress, blocked, completed, aborted.
            progress: The progress percentage (0-100). If not provided, no progress will be updated.
            status_message: A custom status message. If not provided, no status message will be updated.
            next_actions: A list of next actions. If not provided, no next actions will be updated.

        Returns:
            A message indicating success or failure
        """
        if self.role != "field":
            return "Only Field can update mission status."

        # Get mission ID
        mission_id = await MissionManager.get_mission_id(self.context)
        if not mission_id:
            return "No mission associated with this conversation. Unable to update mission status."

        # Update the mission status using MissionManager
        success, status_obj = await MissionManager.update_mission_status(
            context=self.context,
            state=status,
            progress=progress,
            status_message=status_message,
            next_actions=next_actions
        )

        if success and status_obj:
            # Format progress as percentage if available
            progress_text = f" ({progress}% complete)" if progress is not None else ""

            await self.context.send_messages(
                NewConversationMessage(
                    content=f"Mission status updated to '{status}'{progress_text}. All mission participants will see this update.",
                    message_type=MessageType.notice,
                    metadata={},  # Add empty metadata
                )
            )
            return f"Mission status updated to '{status}'{progress_text}."
        else:
            return "Failed to update mission status. Please try again."

    async def mark_criterion_completed(self, goal_index: int, criterion_index: int) -> str:
        """
        Mark a success criterion as completed.

        Args:
            goal_index: The index of the goal (1-based)
            criterion_index: The index of the criterion within the goal (1-based)

        Returns:
            A message indicating success or failure
        """
        if self.role != "field":
            return "Only Field can mark criteria as completed."

        # Get mission ID
        mission_id = await MissionManager.get_mission_id(self.context)
        if not mission_id:
            return "No mission associated with this conversation. Unable to mark criterion as completed."

        # Get existing mission briefing
        briefing = await MissionManager.get_mission_briefing(self.context)
        if not briefing:
            return "No mission briefing found."

        # Adjust indices to be 0-based
        goal_index = goal_index - 1
        criterion_index = criterion_index - 1

        # Validate indices
        if goal_index < 0 or goal_index >= len(briefing.goals):
            return f"Invalid goal index {goal_index + 1}. There are {len(briefing.goals)} goals."

        goal = briefing.goals[goal_index]

        if criterion_index < 0 or criterion_index >= len(goal.success_criteria):
            return f"Invalid criterion index {criterion_index + 1}. Goal '{goal.name}' has {len(goal.success_criteria)} criteria."

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

        # Update briefing metadata
        briefing.updated_at = datetime.utcnow()
        briefing.updated_by = current_user_id
        briefing.version += 1

        # Save the updated briefing
        MissionStorage.write_mission_briefing(mission_id, briefing)

        # Log the criterion completion
        await MissionStorage.log_mission_event(
            context=self.context,
            mission_id=mission_id,
            entry_type=LogEntryType.CRITERION_COMPLETED.value,
            message=f"Success criterion completed: {criterion.description}",
            related_entity_id=None,
            metadata={"goal_name": goal.name, "criterion_description": criterion.description},
        )

        # Update mission status
        status = MissionStorage.read_mission_status(mission_id)

        if status:
            # Count all completed criteria
            completed_criteria = 0
            total_criteria = 0

            for g in briefing.goals:
                total_criteria += len(g.success_criteria)
                completed_criteria += sum(1 for c in g.success_criteria if c.completed)

            # Update status
            status.completed_criteria = completed_criteria
            status.total_criteria = total_criteria

            # Calculate progress percentage
            if total_criteria > 0:
                status.progress_percentage = int((completed_criteria / total_criteria) * 100)

            # Update metadata
            status.updated_at = datetime.utcnow()
            status.updated_by = current_user_id
            status.version += 1

            # Save the updated status
            MissionStorage.write_mission_status(mission_id, status)

            # Notify linked conversations
            await MissionNotifier.notify_mission_update(
                context=self.context,
                mission_id=mission_id,
                update_type="mission_status",
                message=f"Success criterion '{criterion.description}' for goal '{goal.name}' has been marked as completed."
            )

            # Check if all criteria are completed for mission completion
            if completed_criteria == total_criteria and total_criteria > 0:
                await self.context.send_messages(
                    NewConversationMessage(
                        content="🎉 All success criteria have been completed! Consider using the report_mission_completion function to formally complete the mission.",
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

    async def mark_mission_ready_for_field(self) -> str:
        """
        Mark the mission as ready for field operations.
        This is a gate function that transitions from Definition Stage to Working Stage.

        Returns:
            A message indicating success or failure
        """
        if self.role != "hq":
            return "Only HQ can mark a mission as ready for field."

        # Get mission ID
        mission_id = await MissionManager.get_mission_id(self.context)
        if not mission_id:
            return "No mission associated with this conversation. Unable to mark mission as ready for field."

        # Get existing mission briefing and KB
        briefing = MissionStorage.read_mission_briefing(mission_id)
        kb = MissionStorage.read_mission_kb(mission_id)

        if not briefing:
            return "No mission briefing found. Please create one before marking as ready for field."

        if not briefing.goals:
            return "Mission briefing has no goals. Please add at least one goal before marking as ready for field."

        # Check if at least one goal has success criteria
        has_criteria = False
        for goal in briefing.goals:
            if goal.success_criteria:
                has_criteria = True
                break

        if not has_criteria:
            return "No success criteria defined. Please add at least one success criterion to a goal before marking as ready for field."

        # Check if KB has content
        if not kb or not kb.sections:
            return (
                "Mission Knowledge Base is empty. Please add at least one KB section before marking as ready for field."
            )

        # Get or create mission status
        status = MissionStorage.read_mission_status(mission_id)

        # Get current user information
        participants = await self.context.get_participants()
        current_user_id = None

        for participant in participants.participants:
            if participant.role == "user":
                current_user_id = participant.id
                break

        if not current_user_id:
            return "Could not identify current user."

        if not status:
            # Create new status if not found
            status = MissionStatus(
                created_by=current_user_id,
                updated_by=current_user_id,
                conversation_id=str(self.context.id),
                goals=briefing.goals,
            )

            # Calculate total criteria
            total_criteria = 0
            for goal in briefing.goals:
                total_criteria += len(goal.success_criteria)

            status.total_criteria = total_criteria

        # Update status to in_progress
        status.state = MissionState.IN_PROGRESS
        status.status_message = "Mission is now ready for field operations"

        # Add lifecycle metadata
        if not hasattr(status, "lifecycle") or not status.lifecycle:
            status.lifecycle = {}

        status.lifecycle["ready_for_field"] = True
        status.lifecycle["ready_for_field_time"] = datetime.utcnow().isoformat()
        status.lifecycle["ready_for_field_by"] = current_user_id

        # Update metadata
        status.updated_at = datetime.utcnow()
        status.updated_by = current_user_id
        status.version += 1

        # Save the updated status
        MissionStorage.write_mission_status(mission_id, status)

        # Log the gate transition
        await MissionStorage.log_mission_event(
            context=self.context,
            mission_id=mission_id,
            entry_type=LogEntryType.GATE_PASSED.value,
            message="Mission marked as READY FOR FIELD",
            metadata={"gate": "ready_for_field"},
        )

        # Notify linked conversations
        await MissionNotifier.notify_mission_update(
            context=self.context,
            mission_id=mission_id,
            update_type="mission_status",
            message="🔔 **Mission Gate Passed**: HQ has marked the mission as READY FOR FIELD. All mission information is now available and you can begin field operations.",
        )

        await self.context.send_messages(
            NewConversationMessage(
                content="🎯 Mission has been marked as READY FOR FIELD. Field personnel have been notified and can now begin operations.",
                message_type=MessageType.chat,
            )
        )

        return "Mission successfully marked as ready for field operations."

    async def report_mission_completion(self) -> str:
        """
        Report that the mission is complete.
        This is a gate function that concludes the mission lifecycle.

        Returns:
            A message indicating success or failure
        """
        if self.role != "field":
            return "Only Field can report mission completion."

        # Get mission ID
        mission_id = await MissionManager.get_mission_id(self.context)
        if not mission_id:
            return "No mission associated with this conversation. Unable to report mission completion."

        # Get existing mission status
        status = MissionStorage.read_mission_status(mission_id)
        if not status:
            return "No mission status found. Cannot complete mission without a status."

        # Check if all criteria are completed
        if status.completed_criteria < status.total_criteria:
            remaining = status.total_criteria - status.completed_criteria
            return f"Cannot complete mission - {remaining} success criteria are still pending completion."

        # Get current user information
        participants = await self.context.get_participants()
        current_user_id = None

        for participant in participants.participants:
            if participant.role == "user":
                current_user_id = participant.id
                break

        if not current_user_id:
            return "Could not identify current user."

        # Update status to completed
        status.state = MissionState.COMPLETED
        status.progress_percentage = 100
        status.status_message = "Mission is now complete"

        # Add lifecycle metadata
        if not hasattr(status, "lifecycle") or not status.lifecycle:
            status.lifecycle = {}

        status.lifecycle["mission_completed"] = True
        status.lifecycle["mission_completed_time"] = datetime.utcnow().isoformat()
        status.lifecycle["mission_completed_by"] = current_user_id

        # Update metadata
        status.updated_at = datetime.utcnow()
        status.updated_by = current_user_id
        status.version += 1

        # Save the updated status
        MissionStorage.write_mission_status(mission_id, status)

        # Log the gate transition
        await MissionStorage.log_mission_event(
            context=self.context,
            mission_id=mission_id,
            entry_type=LogEntryType.MISSION_COMPLETED.value,
            message="Mission marked as COMPLETED",
            metadata={"gate": "mission_completed"},
        )

        # Notify linked conversations
        await MissionNotifier.notify_mission_update(
            context=self.context,
            mission_id=mission_id,
            update_type="mission_completed",
            message="🎉 **Mission Complete**: Field has reported that all mission objectives have been achieved. The mission is now complete.",
        )

        await self.context.send_messages(
            NewConversationMessage(
                content="🎉 **Mission Complete**: All objectives have been achieved and the mission is now complete. HQ has been notified.",
                message_type=MessageType.chat,
            )
        )

        return "Mission successfully marked as complete. All participants have been notified."

    async def detect_field_request_needs(self, message: str) -> Dict[str, Any]:
        """
        Analyze a user message in context of recent chat history to detect potential field request needs.
        Uses an LLM for sophisticated detection, with keyword fallback.

        Args:
            message: The user message to analyze

        Returns:
            Dict with detection results
        """
        # This is HQ perspective - not used directly but helps model understanding
        if self.role != "field":
            return {"is_field_request": False, "reason": "Only Field conversations can create field requests"}

        # Use a more sophisticated approach with a language model call
        import json
        import logging
        from typing import List

        import openai_client
        from openai.types.chat import ChatCompletionMessageParam

        logger = logging.getLogger(__name__)

        # Define system prompt for the analysis
        system_prompt = """
        You are an analyzer that determines if a field agent's message indicates they need information
        or assistance from HQ. You are part of a mission coordination system where:

        1. Field agents report from deployment locations and may need information from HQ
        2. When field agents need information, they can submit a formal Field Request to HQ
        3. Your job is to detect when a message suggests the field agent needs information/help

        Analyze the chat history and latest message to determine:

        1. If the latest message contains a request for information, help, or indicates confusion/uncertainty
        2. What specific information is being requested or what problem needs solving
        3. A concise title for this potential field request
        4. The priority level (low, medium, high, critical) of the request

        Respond with JSON only:
        {
            "is_field_request": boolean,  // true if message indicates a need for HQ assistance
            "reason": string,  // explanation of your determination
            "potential_title": string,  // a short title for the request (3-8 words)
            "potential_description": string,  // summarized description of the information needed
            "suggested_priority": string,  // "low", "medium", "high", or "critical"
            "confidence": number  // 0.0-1.0 how confident you are in this assessment
        }

        When determining priority:
        - low: routine information, no urgency
        - medium: needed information but not blocking progress
        - high: important information that's blocking progress
        - critical: urgent information needed to address safety or mission-critical issues

        Be conservative - only return is_field_request=true if you're reasonably confident
        the field agent is actually asking for information/help from HQ.
        """

        try:
            # Check if we're in a test environment (Missing parts of context)
            if not hasattr(self.context, "assistant") or self.context.assistant is None:
                return self._simple_keyword_detection(message)

            # Create a simple client for this specific call
            # Note: Using a basic model to keep this detection lightweight
            from semantic_workbench_assistant.assistant_app import BaseModelAssistantConfig

            from .config import AssistantConfigModel

            # Get the config through the proper assistant app context
            assistant_config = BaseModelAssistantConfig(AssistantConfigModel)
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
                        sender_name = "Field Agent"
                        if msg.sender.participant_id == self.context.assistant.id:
                            sender_name = "Assistant"

                        # Add to chat history
                        role = "user" if sender_name == "Field Agent" else "assistant"
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
                messages.append({"role": "user", "content": f"Latest message from Field Agent: {message}"})

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
                    logger.warning("Empty response from LLM for field request detection")
                    return self._simple_keyword_detection(message)

        except Exception as e:
            # Fallback to simple detection if LLM call fails
            logger.exception(f"Error in LLM-based field request detection: {e}")
            return self._simple_keyword_detection(message)

    def _simple_keyword_detection(self, message: str) -> Dict[str, Any]:
        """
        Simple fallback method for request detection using keyword matching.

        Args:
            message: The user message to analyze

        Returns:
            Dict with detection results
        """
        # Simple keyword matching for fallback
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
            return {"is_field_request": False, "reason": "No field request indicators found in message"}

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
            "is_field_request": True,
            "matched_indicators": matched_indicators,
            "potential_title": potential_title,
            "potential_description": message,
            "suggested_priority": priority,
            "confidence": 0.6,  # Medium confidence for keyword-based detection
        }

    async def suggest_next_action(self) -> Dict[str, Any]:
        """
        Suggest the next action the user should take based on mission state.

        Returns:
            Dict with suggestion details
        """
        # Get mission ID
        mission_id = await MissionManager.get_mission_id(self.context)
        if not mission_id:
            # No mission associated with this conversation
            if self.role == "hq":
                return {
                    "suggestion": "create_mission_briefing",
                    "reason": "No mission associated with this conversation. Start by creating a mission briefing.",
                    "priority": "high",
                    "function": "create_mission_briefing",
                    "parameters": {"mission_name": "", "mission_description": ""},
                }
            else:
                return {
                    "suggestion": "wait_for_invitation",
                    "reason": "No mission associated with this conversation. Wait for an invitation from HQ.",
                    "priority": "medium",
                    "function": None,
                }

        # Get mission state information
        briefing = MissionStorage.read_mission_briefing(mission_id)
        kb = MissionStorage.read_mission_kb(mission_id)
        status = MissionStorage.read_mission_status(mission_id)
        requests = MissionStorage.get_all_field_requests(mission_id)

        # Check if mission briefing exists
        if not briefing:
            if self.role == "hq":
                return {
                    "suggestion": "create_mission_briefing",
                    "reason": "No mission briefing found. Start by creating one.",
                    "priority": "high",
                    "function": "create_mission_briefing",
                    "parameters": {"mission_name": "", "mission_description": ""},
                }
            else:
                return {
                    "suggestion": "wait_for_hq",
                    "reason": "No mission briefing found. HQ needs to create one before you can proceed.",
                    "priority": "medium",
                    "function": None,
                }

        # Check if goals exist
        if not briefing.goals:
            if self.role == "hq":
                return {
                    "suggestion": "add_mission_goal",
                    "reason": "Mission briefing has no goals. Add at least one goal with success criteria.",
                    "priority": "high",
                    "function": "add_mission_goal",
                    "parameters": {"goal_name": "", "goal_description": "", "success_criteria": []},
                }
            else:
                return {
                    "suggestion": "wait_for_goals",
                    "reason": "Mission briefing has no goals. HQ needs to add goals before you can proceed.",
                    "priority": "medium",
                    "function": None,
                }

        # Check if KB exists
        if not kb or not kb.sections:
            if self.role == "hq":
                return {
                    "suggestion": "add_kb_section",
                    "reason": "Mission Knowledge Base is empty. Add at least one section with important information.",
                    "priority": "high",
                    "function": "add_kb_section",
                    "parameters": {"title": "", "content": ""},
                }
            else:
                return {
                    "suggestion": "wait_for_kb",
                    "reason": "Mission Knowledge Base is empty. HQ needs to add information before you can proceed.",
                    "priority": "medium",
                    "function": None,
                }

        # Check mission status
        if not status:
            if self.role == "field":
                return {
                    "suggestion": "update_mission_status",
                    "reason": "No mission status found. Create an initial status update.",
                    "priority": "medium",
                    "function": "update_mission_status",
                    "parameters": {
                        "status": "in_progress",
                        "progress": 0,
                        "status_message": "Starting mission operations",
                    },
                }
        else:
            # Check if mission is ready for field
            ready_for_field = (
                hasattr(status, "lifecycle") and status.lifecycle and status.lifecycle.get("ready_for_field", False)
            )

            if not ready_for_field and self.role == "hq":
                # Check if it's ready to mark as ready for field
                has_goals = bool(briefing.goals)
                has_criteria = any(bool(goal.success_criteria) for goal in briefing.goals)
                has_kb = bool(kb and kb.sections)

                if has_goals and has_criteria and has_kb:
                    return {
                        "suggestion": "mark_ready_for_field",
                        "reason": "Mission information is complete. Mark it as ready for field operations.",
                        "priority": "medium",
                        "function": "mark_mission_ready_for_field",
                        "parameters": {},
                    }

            # Check for unresolved field requests for HQ
            if self.role == "hq":
                active_requests = [r for r in requests if r.status == RequestStatus.NEW]
                if active_requests:
                    request = active_requests[0]  # Get the first unresolved request
                    return {
                        "suggestion": "resolve_field_request",
                        "reason": f"There are {len(active_requests)} unresolved field requests. Consider resolving '{request.title}'.",
                        "priority": "high"
                        if request.priority in [RequestPriority.HIGH, RequestPriority.CRITICAL]
                        else "medium",
                        "function": "resolve_field_request",
                        "parameters": {"request_id": request.request_id, "resolution": ""},
                    }

            # For field, check if all criteria are completed for mission completion
            if (
                self.role == "field"
                and status.completed_criteria == status.total_criteria
                and status.total_criteria > 0
            ):
                return {
                    "suggestion": "report_mission_completion",
                    "reason": "All success criteria have been completed. Report mission completion.",
                    "priority": "medium",
                    "function": "report_mission_completion",
                    "parameters": {},
                }

            # For field, suggest marking criteria as completed if any are pending
            if self.role == "field" and status.completed_criteria < status.total_criteria:
                # Find the first uncompleted criterion
                for goal_index, goal in enumerate(briefing.goals):
                    for criterion_index, criterion in enumerate(goal.success_criteria):
                        if not criterion.completed:
                            return {
                                "suggestion": "mark_criterion_completed",
                                "reason": "Update progress by marking completed success criteria.",
                                "priority": "low",
                                "function": "mark_criterion_completed",
                                "parameters": {
                                    "goal_index": goal_index + 1,  # 1-based indexing
                                    "criterion_index": criterion_index + 1,  # 1-based indexing
                                },
                            }

        # Default suggestions based on role
        if self.role == "hq":
            return {
                "suggestion": "monitor_progress",
                "reason": "Monitor field operations and respond to any new field requests.",
                "priority": "low",
                "function": None,
            }
        else:
            return {
                "suggestion": "update_status",
                "reason": "Continue field operations and update mission progress as you make advancements.",
                "priority": "low",
                "function": "update_mission_status",
                "parameters": {"status": "in_progress"},
            }


# Factory function to create a role-specific MissionTools instance
async def get_mission_tools(context: ConversationContext, role: str) -> MissionTools:
    """
    Get an instance of MissionTools for a given context and role.

    Args:
        context: The conversation context
        role: The assistant's role ("hq" or "field")

    Returns:
        An instance of MissionTools
    """
    return MissionTools(context, role)
