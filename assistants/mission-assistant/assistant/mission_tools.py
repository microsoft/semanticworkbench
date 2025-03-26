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

from .artifact_messaging import ArtifactManager, ArtifactMessenger
from .artifacts import (
    ArtifactType,
    FieldRequest,
    LogEntryType, 
    MissionBriefing,
    MissionKB,
    MissionState,
    MissionStatus,
    RequestPriority,
    RequestStatus,
)
from .command_processor import (
    handle_add_goal_command,
    handle_add_kb_section_command,
)
from .mission import ConversationClientManager, MissionStateManager
from .mission_manager import MissionManager, MissionRole

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

        # Fetch mission artifacts from the shared artifact storage system
        # ArtifactMessenger provides access to artifacts across linked conversations

        output = []

        # Get mission briefing if requested
        if info_type in ["all", "briefing"]:
            briefings = await ArtifactMessenger.get_artifacts_by_type(self.context, MissionBriefing)

            if briefings:
                briefing = briefings[0]  # Most recent briefing

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
            kb_artifacts = await ArtifactMessenger.get_artifacts_by_type(self.context, MissionKB)

            if kb_artifacts and kb_artifacts[0].sections:
                kb = kb_artifacts[0]  # Most recent KB

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
            status_artifacts = await ArtifactMessenger.get_artifacts_by_type(self.context, MissionStatus)

            if status_artifacts:
                status = status_artifacts[0]  # Most recent status

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
            requests = await ArtifactMessenger.get_artifacts_by_type(self.context, FieldRequest)

            if requests:
                output.append("\n## Field Requests\n")

                # Group requests by status
                active_requests = [r for r in requests if r.status not in ["resolved", "cancelled"]]
                resolved_requests = [r for r in requests if r.status in ["resolved", "cancelled"]]

                if active_requests:
                    output.append("### Active Requests\n")

                    for request in active_requests:
                        priority_marker = {
                            "low": "🔹",
                            "medium": "🔶",
                            "high": "🔴",
                            "critical": "⚠️",
                        }.get(request.priority, "🔹")

                        # Include request ID for easy reference when resolving
                        output.append(f"{priority_marker} **{request.title}** ({request.status})")
                        output.append(f"  ID: `{request.artifact_id}`")
                        output.append(f"  {request.description}")

                        if request.updates:
                            last_update = request.updates[-1]
                            output.append(f"  *Last update: {last_update.get('message', '')}*")

                        output.append("")

                if resolved_requests and info_type == "requests":
                    output.append("### Resolved Requests\n")

                    for request in resolved_requests[:5]:  # Show only the 5 most recent
                        output.append(f"✅ **{request.title}** ({request.status})")
                        output.append(f"  ID: `{request.artifact_id}`")

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
        mission_id = await MissionManager.get_or_create_mission(
            self.context, mission_name, MissionRole.HQ
        )

        if not mission_id:
            return "Failed to create or retrieve mission. Please try again."

        # Create a new mission briefing artifact using ArtifactManager
        # This will be visible to both HQ and Field conversations
        success, briefing = await ArtifactManager.create_mission_briefing(
            self.context, mission_name, mission_description
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

        # Retrieve the existing mission briefing to add goals to it
        # MissionBriefing is the primary artifact that defines mission objectives

        # Get existing mission briefing
        briefings = await ArtifactMessenger.get_artifacts_by_type(self.context, MissionBriefing)

        if not briefings:
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

        Args:
            request_id: ID of the field request to resolve
            resolution: Resolution information to add to the request

        Returns:
            A message indicating success or failure
        """
        if self.role != "hq":
            return "Only HQ can resolve field requests."

        # Resolve the field request using ArtifactManager
        # This updates the request status and notifies the field conversation

        success, field_request = await ArtifactManager.resolve_field_request(self.context, request_id, resolution)

        if success and field_request:
            # This notification is sent to Field by the resolve_field_request method
            return f"Field request '{field_request.title}' has been resolved."
        else:
            return "Failed to resolve the field request. Make sure the request ID is correct."

    async def create_field_request(
        self, title: str, description: str, priority: Literal["low", "medium", "high", "critical"]
    ) -> str:
        """
        Create a field request for information or to report a blocker.

        Args:
            title: The title of the request
            description: A description of the request
            priority: The priority of the request. Must be one of: low, medium, high, critical.

        Returns:
            A message indicating success or failure
        """
        if self.role != "field":
            return "Only Field can create field requests."

        # Create a field request with specified priority level
        # RequestPriority helps HQ understand urgency (LOW, MEDIUM, HIGH, CRITICAL)

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

        # Create the field request
        success, request = await ArtifactManager.create_field_request(self.context, title, description, priority_enum)

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

        # Handle optional parameters for status update
        # Only specified parameters will be updated in the mission status artifact
        # The mission status is shared between HQ and field to maintain synchronization

        # Update the mission status
        success, status_obj = await ArtifactManager.update_mission_status(
            self.context, status=status, progress=progress, status_message=status_message, next_actions=next_actions
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

        # Access mission briefing and track criterion completion
        # Updates are logged with ArtifactType.MISSION_BRIEFING and LogEntryType.CRITERION_COMPLETED
        # for audit trail and notification purposes

        # Get existing mission briefing
        briefings = await ArtifactMessenger.get_artifacts_by_type(self.context, MissionBriefing)

        if not briefings:
            return "No mission briefing found."

        briefing = briefings[0]

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
        # Explicitly not using current_user_name for now to avoid F841 lint error

        for participant in participants.participants:
            if participant.role == "user":
                current_user_id = participant.id
                # Store name if needed later
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
        success = await ArtifactMessenger.save_artifact(self.context, briefing)

        if not success:
            return "Failed to update mission briefing with completed criterion. Please try again."

        # Log the criterion completion
        await ArtifactMessenger.log_artifact_update(
            self.context,
            briefing.artifact_id,
            ArtifactType.MISSION_BRIEFING,
            current_user_id,
            briefing.version,
            LogEntryType.CRITERION_COMPLETED,
            f"Success criterion completed: {criterion.description}",
            {"goal_name": goal.name, "criterion_description": criterion.description},
        )

        # Update mission status
        statuses = await ArtifactMessenger.get_artifacts_by_type(self.context, MissionStatus)

        if statuses:
            status = statuses[0]

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
            await ArtifactMessenger.save_artifact(self.context, status)

            # Share with linked conversations
            links = await MissionStateManager.get_links(self.context)
            for conv_id in links.linked_conversations:
                if conv_id != str(self.context.id):
                    await ArtifactMessenger.send_artifact(self.context, briefing, conv_id)
                    await ArtifactMessenger.send_artifact(self.context, status, conv_id)

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

        # Verify mission readiness requirements before marking as ready for field
        # This is a critical gate transition that moves the mission from planning to operational phase
        # Updates MissionStatus and notifies linked conversations via MissionStateManager

        # Get existing mission briefing and KB
        briefings = await ArtifactMessenger.get_artifacts_by_type(self.context, MissionBriefing)

        kb_artifacts = await ArtifactMessenger.get_artifacts_by_type(self.context, MissionKB)

        if not briefings:
            return "No mission briefing found. Please create one before marking as ready for field."

        briefing = briefings[0]

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
        if not kb_artifacts or not kb_artifacts[0].sections:
            return (
                "Mission Knowledge Base is empty. Please add at least one KB section before marking as ready for field."
            )

        # Get or create mission status
        statuses = await ArtifactMessenger.get_artifacts_by_type(self.context, MissionStatus)

        # Get current user information
        participants = await self.context.get_participants()
        current_user_id = None

        for participant in participants.participants:
            if participant.role == "user":
                current_user_id = participant.id
                break

        if not current_user_id:
            return "Could not identify current user."

        mission_status = None
        if statuses:
            mission_status = statuses[0]
        else:
            # Create new status if not found
            mission_status = MissionStatus(
                created_by=current_user_id,
                updated_by=current_user_id,
                conversation_id=str(self.context.id),
                goals=briefing.goals,
            )

            # Calculate total criteria
            total_criteria = 0
            for goal in briefing.goals:
                total_criteria += len(goal.success_criteria)

            mission_status.total_criteria = total_criteria

        # Update status to in_progress
        mission_status.state = MissionState.IN_PROGRESS
        mission_status.status_message = "Mission is now ready for field operations"

        # Add lifecycle metadata
        if not hasattr(mission_status, "lifecycle") or not mission_status.lifecycle:
            mission_status.lifecycle = {}

        mission_status.lifecycle["ready_for_field"] = True
        mission_status.lifecycle["ready_for_field_time"] = datetime.utcnow().isoformat()
        mission_status.lifecycle["ready_for_field_by"] = current_user_id

        # Update metadata
        mission_status.updated_at = datetime.utcnow()
        mission_status.updated_by = current_user_id
        mission_status.version += 1

        # Save the updated status
        success = await ArtifactMessenger.save_artifact(self.context, mission_status)

        if not success:
            return "Failed to update mission status. Please try again."

        # Log the gate transition
        await ArtifactMessenger.log_artifact_update(
            self.context,
            mission_status.artifact_id,
            ArtifactType.MISSION_STATUS,
            current_user_id,
            mission_status.version,
            LogEntryType.GATE_PASSED,
            "Mission marked as READY FOR FIELD",
            {"gate": "ready_for_field"},
        )

        # Share with linked conversations
        links = await MissionStateManager.get_links(self.context)

        # Prepare notification for field conversations
        for conv_id in links.linked_conversations:
            if conv_id != str(self.context.id):
                # Send status update
                await ArtifactMessenger.send_artifact(self.context, mission_status, conv_id)

                # Send notification to field conversation
                target_client = ConversationClientManager.get_conversation_client(self.context, conv_id)

                if target_client:
                    await target_client.send_messages(
                        NewConversationMessage(
                            content="🔔 **Mission Gate Passed**: HQ has marked the mission as READY FOR FIELD. All mission information is now available and you can begin field operations.",
                            message_type=MessageType.notice,
                        )
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

        # Import here to avoid circular dependencies
        from .artifact_messaging import ArtifactMessenger
        from .artifacts import ArtifactType, LogEntryType
        from .mission import MissionStateManager

        # Get existing mission status
        statuses = await ArtifactMessenger.get_artifacts_by_type(self.context, MissionStatus)

        if not statuses:
            return "No mission status found. Cannot complete mission without a status."

        mission_status = statuses[0]

        # Check if all criteria are completed
        if mission_status.completed_criteria < mission_status.total_criteria:
            remaining = mission_status.total_criteria - mission_status.completed_criteria
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
        mission_status.state = MissionState.COMPLETED
        mission_status.progress_percentage = 100
        mission_status.status_message = "Mission is now complete"

        # Add lifecycle metadata
        if not hasattr(mission_status, "lifecycle") or not mission_status.lifecycle:
            mission_status.lifecycle = {}

        mission_status.lifecycle["mission_completed"] = True
        mission_status.lifecycle["mission_completed_time"] = datetime.utcnow().isoformat()
        mission_status.lifecycle["mission_completed_by"] = current_user_id

        # Update metadata
        mission_status.updated_at = datetime.utcnow()
        mission_status.updated_by = current_user_id
        mission_status.version += 1

        # Save the updated status
        success = await ArtifactMessenger.save_artifact(self.context, mission_status)

        if not success:
            return "Failed to update mission status. Please try again."

        # Log the gate transition
        await ArtifactMessenger.log_artifact_update(
            self.context,
            mission_status.artifact_id,
            ArtifactType.MISSION_STATUS,
            current_user_id,
            mission_status.version,
            LogEntryType.MISSION_COMPLETED,
            "Mission marked as COMPLETED",
            {"gate": "mission_completed"},
        )

        # Share with linked conversations
        links = await MissionStateManager.get_links(self.context)

        # Prepare notification for HQ conversations
        for conv_id in links.linked_conversations:
            if conv_id != str(self.context.id):
                # Send status update
                await ArtifactMessenger.send_artifact(self.context, mission_status, conv_id)

                # Send notification to HQ conversation
                target_client = ConversationClientManager.get_conversation_client(self.context, conv_id)

                if target_client:
                    await target_client.send_messages(
                        NewConversationMessage(
                            content="🎉 **Mission Complete**: Field has reported that all mission objectives have been achieved. The mission is now complete.",
                            message_type=MessageType.notice,
                        )
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
        Analyze a user message to detect potential field request needs.
        Used to proactively suggest creating field requests.

        Args:
            message: The user message to analyze

        Returns:
            Dict with detection results
        """
        # This is HQ perspective - not used directly but helps model understanding
        if self.role != "field":
            return {"is_field_request": False, "reason": "Only Field conversations can create field requests"}

        # Simple keyword matching for demonstration purposes
        # In a full implementation, this could use a more sophisticated approach
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
        }

    async def suggest_next_action(self) -> Dict[str, Any]:
        """
        Suggest the next action the user should take based on mission state.

        Returns:
            Dict with suggestion details
        """
        # Analyze mission state to determine appropriate next actions
        # Based on current briefing, KB, status, and pending field requests
        # Uses RequestPriority and RequestStatus to prioritize suggestions

        # Get mission state information
        briefings = await ArtifactMessenger.get_artifacts_by_type(self.context, MissionBriefing)

        kb_artifacts = await ArtifactMessenger.get_artifacts_by_type(self.context, MissionKB)

        statuses = await ArtifactMessenger.get_artifacts_by_type(self.context, MissionStatus)

        requests = await ArtifactMessenger.get_artifacts_by_type(self.context, FieldRequest)

        # Check if mission briefing exists
        if not briefings:
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

        briefing = briefings[0]

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
        if not kb_artifacts or not kb_artifacts[0].sections:
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
        if not statuses:
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
            status = statuses[0]

            # Check if mission is ready for field
            ready_for_field = (
                hasattr(status, "lifecycle") and status.lifecycle and status.lifecycle.get("ready_for_field", False)
            )

            if not ready_for_field and self.role == "hq":
                # Check if it's ready to mark as ready for field
                has_goals = bool(briefing.goals)
                has_criteria = any(bool(goal.success_criteria) for goal in briefing.goals)
                has_kb = bool(kb_artifacts and kb_artifacts[0].sections)

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
                        "parameters": {"request_id": request.artifact_id, "resolution": ""},
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
