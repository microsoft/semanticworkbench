"""
Command processor for the mission assistant.

This module provides a unified framework for processing commands in the mission assistant.
It defines a command registry, command handlers for both HQ and Field modes, and authorization
controls based on user roles.
"""

import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Awaitable

from semantic_workbench_api_model.workbench_model import ConversationMessage, MessageType, NewConversationMessage
from semantic_workbench_assistant.assistant_app import ConversationContext

from .artifact_messaging import ArtifactManager, ArtifactMessenger
from .artifacts import (
    ArtifactType,
    FieldRequest,
    MissionBriefing,
    MissionGoal,
    MissionKB,
    MissionStatus,
    RequestPriority,
    SuccessCriterion,
)
from .mission_manager import MissionManager
from .mission import MissionStateManager

logger = logging.getLogger(__name__)

# Command handler function type
CommandHandlerType = Callable[[ConversationContext, ConversationMessage, List[str]], Awaitable[None]]


class CommandRegistry:
    """Registry for command handlers with authorization controls."""

    def __init__(self):
        """Initialize the command registry."""
        self.commands: Dict[str, Dict[str, Any]] = {}
        
    def register_command(
        self,
        command_name: str,
        handler: CommandHandlerType,
        description: str,
        usage: str,
        example: str,
        authorized_roles: Optional[List[str]] = None,
    ) -> None:
        """
        Register a command handler.
        
        Args:
            command_name: The command name (without the '/')
            handler: The function that handles the command
            description: A brief description of what the command does
            usage: The command usage format
            example: An example of how to use the command
            authorized_roles: List of roles that can use this command (None for all)
        """
        self.commands[command_name] = {
            "handler": handler,
            "description": description,
            "usage": usage,
            "example": example,
            "authorized_roles": authorized_roles,
        }
    
    def is_authorized(self, command_name: str, role: str) -> bool:
        """
        Check if a role is authorized to use a command.
        
        Args:
            command_name: The command name
            role: The user role
            
        Returns:
            True if authorized, False otherwise
        """
        if command_name not in self.commands:
            return False
            
        authorized_roles = self.commands[command_name]["authorized_roles"]
        if authorized_roles is None:
            return True  # Command available to all roles
            
        return role in authorized_roles
    
    def get_command_help(self, command_name: str) -> Optional[Dict[str, str]]:
        """
        Get help information for a command.
        
        Args:
            command_name: The command name
            
        Returns:
            Dictionary with help information or None if command not found
        """
        if command_name not in self.commands:
            return None
            
        return {
            "description": self.commands[command_name]["description"],
            "usage": self.commands[command_name]["usage"],
            "example": self.commands[command_name]["example"],
        }
    
    def get_commands_for_role(self, role: str) -> Dict[str, Dict[str, Any]]:
        """
        Get all commands available for a specific role.
        
        Args:
            role: The user role
            
        Returns:
            Dictionary of commands available to the role
        """
        return {
            name: cmd for name, cmd in self.commands.items() 
            if self.is_authorized(name, role)
        }
    
    async def process_command(
        self, context: ConversationContext, message: ConversationMessage, role: str
    ) -> bool:
        """
        Process a command message.
        
        Args:
            context: The conversation context
            message: The command message
            role: The user's role (hq or field)
            
        Returns:
            True if command was processed, False otherwise
        """
        # Split the command and extract the command name
        content = message.content.strip()
        if not content.startswith('/'):
            return False
            
        # Extract command name and arguments
        parts = content.split()
        command_name = parts[0][1:]  # Remove the '/' prefix
        args = parts[1:] if len(parts) > 1 else []
        
        # Check if command exists
        if command_name not in self.commands:
            await context.send_messages(
                NewConversationMessage(
                    content=f"Unknown command: /{command_name}. Type /help to see available commands.",
                    message_type=MessageType.notice,
                )
            )
            return True
            
        # Check if user is authorized to use this command
        if not self.is_authorized(command_name, role):
            await context.send_messages(
                NewConversationMessage(
                    content=f"The /{command_name} command is only available to {' or '.join(self.commands[command_name]['authorized_roles'])} roles. You are in {role.upper()} mode.",
                    message_type=MessageType.notice,
                )
            )
            return True
            
        try:
            # Execute the command handler
            await self.commands[command_name]["handler"](context, message, args)
            return True
        except Exception as e:
            logger.exception(f"Error processing command /{command_name}: {e}")
            await context.send_messages(
                NewConversationMessage(
                    content=f"Error processing command /{command_name}: {str(e)}",
                    message_type=MessageType.notice,
                )
            )
            return True


# Initialize the command registry
command_registry = CommandRegistry()


# Command handler implementations

async def handle_help_command(
    context: ConversationContext, message: ConversationMessage, args: List[str]
) -> None:
    """Handle the help command."""
    # Get the conversation's role
    from .mission_manager import MissionManager
    
    # First check conversation metadata
    conversation = await context.get_conversation()
    metadata = conversation.metadata or {}
    metadata_role = metadata.get("mission_role")
    
    # Then check the stored role from mission storage - this is the authoritative source
    stored_role = await MissionManager.get_conversation_role(context)
    stored_role_value = stored_role.value if stored_role else None
    
    # Log the roles for debugging
    logger.debug(f"Role detection in help command - Metadata role: {metadata_role}, Stored role: {stored_role_value}")
    
    # If we have a stored role but metadata is different, use stored role (more reliable)
    if stored_role_value and metadata_role != stored_role_value:
        logger.warning(f"Role mismatch in help command! Metadata: {metadata_role}, Storage: {stored_role_value}")
        role = stored_role_value
    else:
        # Otherwise use metadata or default to HQ
        role = metadata_role or "hq"  # Default to HQ if not set
    
    # If a specific command is specified, show detailed help for that command
    if args:
        command_name = args[0]
        if command_name.startswith('/'):
            command_name = command_name[1:]  # Remove the '/' prefix
            
        help_info = command_registry.get_command_help(command_name)
        
        if help_info and command_registry.is_authorized(command_name, role):
            await context.send_messages(
                NewConversationMessage(
                    content=f"""## Help: /{command_name}

{help_info['description']}

**Usage:** {help_info['usage']}

**Example:** {help_info['example']}
""",
                    message_type=MessageType.chat,
                )
            )
        else:
            await context.send_messages(
                NewConversationMessage(
                    content=f"No help available for command /{command_name} or you're not authorized to use it.",
                    message_type=MessageType.notice,
                )
            )
        return
    
    # Otherwise show all available commands for the current role
    available_commands = command_registry.get_commands_for_role(role)
    
    # Format help text based on role
    if role == "hq":
        help_text = "## Mission Assistant Commands (HQ Mode)\n\n"
    else:
        help_text = "## Mission Assistant Commands (Field Mode)\n\n"
    
    # Group commands by category
    mission_commands = []
    kb_commands = []
    request_commands = []
    team_commands = []
    status_commands = []
    info_commands = []
    
    for name, cmd in available_commands.items():
        command_entry = f"- `/{name}`: {cmd['description']}"
        
        if "create-briefing" in name or "add-goal" in name:
            mission_commands.append(command_entry)
        elif "kb" in name:
            kb_commands.append(command_entry)
        elif "request" in name:
            request_commands.append(command_entry)
        elif "invite" in name or "join" in name or "list-participants" in name or "revoke" in name:
            team_commands.append(command_entry)
        elif "status" in name or "update" in name:
            status_commands.append(command_entry)
        else:
            info_commands.append(command_entry)
    
    # Add sections to help text if they have commands
    if mission_commands:
        help_text += "### Mission Configuration\n" + "\n".join(mission_commands) + "\n\n"
    
    if kb_commands:
        help_text += "### Knowledge Base Management\n" + "\n".join(kb_commands) + "\n\n"
    
    if team_commands:
        help_text += "### Team Management\n" + "\n".join(team_commands) + "\n\n"
    
    if request_commands:
        help_text += "### Field Request Management\n" + "\n".join(request_commands) + "\n\n"
    
    if status_commands:
        help_text += "### Status Management\n" + "\n".join(status_commands) + "\n\n"
    
    if info_commands:
        help_text += "### Information\n" + "\n".join(info_commands) + "\n\n"
    
    # Add role-specific guidance
    if role == "hq":
        help_text += "As HQ, you are responsible for defining the mission, creating mission knowledge, and coordinating field personnel."
    else:
        help_text += "As Field personnel, you can access mission knowledge, request information, and report progress on mission goals."
    
    await context.send_messages(
        NewConversationMessage(
            content=help_text,
            message_type=MessageType.chat,
        )
    )


async def handle_create_briefing_command(
    context: ConversationContext, message: ConversationMessage, args: List[str]
) -> None:
    """Handle the create-briefing command."""
    # Parse the command
    content = message.content.strip()[len("/create-briefing") :].strip()
    
    if not content or "|" not in content:
        await context.send_messages(
            NewConversationMessage(
                content="Please provide a mission name and description in the format: `/create-briefing Mission Name|Mission description here`",
                message_type=MessageType.notice,
            )
        )
        return
    
    # Extract mission name and description
    try:
        mission_name, mission_description = content.split("|", 1)
        mission_name = mission_name.strip()
        mission_description = mission_description.strip()
        
        if not mission_name or not mission_description:
            raise ValueError("Both mission name and description are required")
        
        # Create the mission briefing
        success, briefing = await ArtifactManager.create_mission_briefing(context, mission_name, mission_description)
        
        if success and briefing:
            await context.send_messages(
                NewConversationMessage(
                    content=f"Mission briefing '{mission_name}' created successfully. You can now add goals with `/add-goal` and share the mission with `/invite`.",
                    message_type=MessageType.chat,
                )
            )
        else:
            await context.send_messages(
                NewConversationMessage(
                    content="Failed to create mission briefing. Please try again.",
                    message_type=MessageType.notice,
                )
            )
    except Exception as e:
        logger.exception(f"Error creating mission briefing: {e}")
        await context.send_messages(
            NewConversationMessage(
                content=f"Error creating mission briefing: {str(e)}",
                message_type=MessageType.notice,
            )
        )


async def handle_add_goal_command(
    context: ConversationContext, message: ConversationMessage, args: List[str]
) -> None:
    """Handle the add-goal command."""
    # Parse the command
    content = message.content.strip()[len("/add-goal") :].strip()
    
    if not content or "|" not in content:
        await context.send_messages(
            NewConversationMessage(
                content="Please provide a goal name, description, and success criteria in the format: `/add-goal Goal Name|Goal description|Success criteria 1;Success criteria 2`",
                message_type=MessageType.notice,
            )
        )
        return
    
    # Extract goal details
    try:
        parts = content.split("|")
        
        if len(parts) < 2:
            raise ValueError("Goal name and description are required")
        
        goal_name = parts[0].strip()
        goal_description = parts[1].strip()
        
        # Parse success criteria if provided
        success_criteria = []
        if len(parts) > 2 and parts[2].strip():
            criteria_list = parts[2].strip().split(";")
            success_criteria = [c.strip() for c in criteria_list if c.strip()]
        
        if not goal_name or not goal_description:
            raise ValueError("Both goal name and description are required")
        
        # Get existing mission briefing
        briefings = await ArtifactMessenger.get_artifacts_by_type(context, MissionBriefing)
        
        if not briefings:
            await context.send_messages(
                NewConversationMessage(
                    content="No mission briefing found. Please create one first with `/create-briefing`.",
                    message_type=MessageType.notice,
                )
            )
            return
        
        # Get the most recent briefing
        briefing = briefings[0]
        
        # Create success criterion objects
        criterion_objects = [SuccessCriterion(description=criterion) for criterion in success_criteria]
        
        # Create the goal
        goal = MissionGoal(
            name=goal_name,
            description=goal_description,
            priority=len(briefing.goals) + 1,  # Set priority based on order added
            success_criteria=criterion_objects,
        )
        
        # Add to the briefing
        briefing.goals.append(goal)
        
        # Update briefing metadata
        participants = await context.get_participants()
        current_user_id = None
        for participant in participants.participants:
            if participant.role == "user":
                current_user_id = participant.id
                break
        
        if not current_user_id:
            raise ValueError("Could not identify current user")
        
        briefing.updated_at = datetime.now()
        briefing.updated_by = current_user_id
        briefing.version += 1
        
        # Save the updated briefing
        success = await ArtifactMessenger.save_artifact(context, briefing)
        
        if success:
            # Log the update
            await ArtifactMessenger.log_artifact_update(
                context,
                briefing.artifact_id,
                ArtifactType.MISSION_BRIEFING,
                current_user_id,
                briefing.version,
            )
            
            # Share with linked conversations
            links = await MissionStateManager.get_links(context)
            for conv_id in links.linked_conversations:
                if conv_id != str(context.id):
                    await ArtifactMessenger.send_artifact(context, briefing, conv_id)
            
            # Build success criteria message
            criteria_msg = ""
            if success_criteria:
                criteria_list = "\n".join([f"- {c}" for c in success_criteria])
                criteria_msg = f"\n\nSuccess Criteria:\n{criteria_list}"
            
            await context.send_messages(
                NewConversationMessage(
                    content=f"Goal '{goal_name}' added to mission briefing successfully.{criteria_msg}",
                    message_type=MessageType.chat,
                )
            )
        else:
            await context.send_messages(
                NewConversationMessage(
                    content="Failed to update mission briefing with new goal. Please try again.",
                    message_type=MessageType.notice,
                )
            )
    except Exception as e:
        logger.exception(f"Error adding goal: {e}")
        await context.send_messages(
            NewConversationMessage(
                content=f"Error adding goal: {str(e)}",
                message_type=MessageType.notice,
            )
        )


async def handle_add_kb_section_command(
    context: ConversationContext, message: ConversationMessage, args: List[str]
) -> None:
    """Handle the add-kb-section command."""
    # Parse the command
    content = message.content.strip()[len("/add-kb-section") :].strip()
    
    if not content or "|" not in content:
        await context.send_messages(
            NewConversationMessage(
                content="Please provide a section title and content in the format: `/add-kb-section Section Title|Section content here`",
                message_type=MessageType.notice,
            )
        )
        return
    
    # Extract section title and content
    try:
        title, section_content = content.split("|", 1)
        title = title.strip()
        section_content = section_content.strip()
        
        if not title or not section_content:
            raise ValueError("Both section title and content are required")
        
        # Get existing KB or create new one
        kb_artifacts = await ArtifactMessenger.get_artifacts_by_type(context, MissionKB)
        
        kb_id = None
        if kb_artifacts:
            kb_id = kb_artifacts[0].artifact_id  # Use the most recent KB
        
        # Add the section
        success, kb = await ArtifactManager.create_kb_section(context, kb_id, title, section_content)
        
        if success and kb:
            await context.send_messages(
                NewConversationMessage(
                    content=f"Knowledge base section '{title}' added successfully. This information is now available to all mission participants.",
                    message_type=MessageType.chat,
                )
            )
        else:
            await context.send_messages(
                NewConversationMessage(
                    content="Failed to add knowledge base section. Please try again.",
                    message_type=MessageType.notice,
                )
            )
    except Exception as e:
        logger.exception(f"Error adding KB section: {e}")
        await context.send_messages(
            NewConversationMessage(
                content=f"Error adding knowledge base section: {str(e)}",
                message_type=MessageType.notice,
            )
        )


async def handle_request_info_command(
    context: ConversationContext, message: ConversationMessage, args: List[str]
) -> None:
    """Handle the request-info command."""
    # Parse the command
    content = message.content.strip()[len("/request-info") :].strip()
    
    if not content or "|" not in content:
        await context.send_messages(
            NewConversationMessage(
                content="Please provide a request title and description in the format: `/request-info Request Title|Description of what you need|priority` (priority is optional: low, medium, high, critical)",
                message_type=MessageType.notice,
            )
        )
        return
    
    # Extract request details
    try:
        parts = content.split("|")
        
        title = parts[0].strip()
        description = parts[1].strip() if len(parts) > 1 else ""
        priority_str = parts[2].strip().lower() if len(parts) > 2 else "medium"
        
        if not title or not description:
            raise ValueError("Both request title and description are required")
        
        # Map priority string to enum
        priority_map = {
            "low": RequestPriority.LOW,
            "medium": RequestPriority.MEDIUM,
            "high": RequestPriority.HIGH,
            "critical": RequestPriority.CRITICAL,
        }
        priority = priority_map.get(priority_str, RequestPriority.MEDIUM)
        
        # Create the field request
        success, request = await ArtifactManager.create_field_request(context, title, description, priority)
        
        if success and request:
            await context.send_messages(
                NewConversationMessage(
                    content=f"Field request '{title}' created successfully with {priority_str} priority. HQ has been notified and will respond to your request.",
                    message_type=MessageType.chat,
                )
            )
        else:
            await context.send_messages(
                NewConversationMessage(
                    content="Failed to create field request. Please try again.",
                    message_type=MessageType.notice,
                )
            )
    except Exception as e:
        logger.exception(f"Error creating field request: {e}")
        await context.send_messages(
            NewConversationMessage(
                content=f"Error creating field request: {str(e)}",
                message_type=MessageType.notice,
            )
        )


async def handle_update_status_command(
    context: ConversationContext, message: ConversationMessage, args: List[str]
) -> None:
    """Handle the update-status command."""
    # Parse the command
    content = message.content.strip()[len("/update-status") :].strip()
    
    if not content:
        await context.send_messages(
            NewConversationMessage(
                content="Please provide status information in the format: `/update-status status|progress|message` (e.g., `/update-status in_progress|75|Making good progress on objectives`)",
                message_type=MessageType.notice,
            )
        )
        return
    
    # Extract status details
    try:
        parts = content.split("|")
        
        status = parts[0].strip() if parts else None
        progress_str = parts[1].strip() if len(parts) > 1 else None
        status_message = parts[2].strip() if len(parts) > 2 else None
        
        # Convert progress to int if provided
        progress = None
        if progress_str:
            try:
                progress = int(progress_str)
                # Ensure progress is between 0-100
                progress = max(0, min(100, progress))
            except ValueError:
                progress = None
        
        # Update the mission status
        success, status_obj = await ArtifactManager.update_mission_status(
            context, status=status, progress=progress, status_message=status_message
        )
        
        if success and status_obj:
            # Format progress as percentage if available
            progress_text = f" ({progress}% complete)" if progress is not None else ""
            
            await context.send_messages(
                NewConversationMessage(
                    content=f"Mission status updated to '{status}'{progress_text}. All mission participants will see this update.",
                    message_type=MessageType.chat,
                )
            )
        else:
            await context.send_messages(
                NewConversationMessage(
                    content="Failed to update mission status. Please try again.",
                    message_type=MessageType.notice,
                )
            )
    except Exception as e:
        logger.exception(f"Error updating mission status: {e}")
        await context.send_messages(
            NewConversationMessage(
                content=f"Error updating mission status: {str(e)}",
                message_type=MessageType.notice,
            )
        )


async def handle_resolve_request_command(
    context: ConversationContext, message: ConversationMessage, args: List[str]
) -> None:
    """Handle the resolve-request command."""
    # Parse the command
    content = message.content.strip()[len("/resolve-request") :].strip()
    
    if not content or "|" not in content:
        await context.send_messages(
            NewConversationMessage(
                content="Please provide a request ID and resolution in the format: `/resolve-request request_id|Resolution information here`",
                message_type=MessageType.notice,
            )
        )
        return
    
    try:
        # Extract request ID and resolution
        request_id, resolution = content.split("|", 1)
        request_id = request_id.strip()
        resolution = resolution.strip()
        
        if not request_id or not resolution:
            raise ValueError("Both request ID and resolution are required")
        
        # Show all field requests if the user doesn't know the ID
        if request_id.lower() == "list":
            await context.send_messages(
                NewConversationMessage(
                    content="Here are the active field requests:",
                    message_type=MessageType.notice,
                )
            )
            
            # Get field requests
            from .artifacts import FieldRequest
            requests = await ArtifactMessenger.get_artifacts_by_type(context, FieldRequest)
            
            # Filter for active requests
            active_requests = [r for r in requests if r.status != "resolved"]
            
            if active_requests:
                request_list = ["## Active Field Requests\n"]
                
                for request in active_requests:
                    request_list.append(f"**ID**: `{request.artifact_id}`")
                    request_list.append(f"**Title**: {request.title}")
                    request_list.append(f"**Priority**: {request.priority}")
                    request_list.append(f"**Description**: {request.description}")
                    request_list.append("")
                
                await context.send_messages(
                    NewConversationMessage(
                        content="\n".join(request_list),
                        message_type=MessageType.chat,
                    )
                )
            else:
                await context.send_messages(
                    NewConversationMessage(
                        content="No active field requests found.",
                        message_type=MessageType.notice,
                    )
                )
            return
        
        # Resolve the field request
        success, field_request = await ArtifactManager.resolve_field_request(context, request_id, resolution)
        
        if success and field_request:
            await context.send_messages(
                NewConversationMessage(
                    content=f"Field request '{field_request.title}' has been resolved. The Field has been notified.",
                    message_type=MessageType.chat,
                )
            )
        else:
            await context.send_messages(
                NewConversationMessage(
                    content="Failed to resolve the field request. Make sure the request ID is correct and the request is not already resolved.",
                    message_type=MessageType.notice,
                )
            )
            
            # Suggest listing all requests to help the user
            await context.send_messages(
                NewConversationMessage(
                    content="Use `/resolve-request list|` to view all field requests and their IDs.",
                    message_type=MessageType.notice,
                )
            )
    except Exception as e:
        logger.exception(f"Error resolving field request: {e}")
        await context.send_messages(
            NewConversationMessage(
                content=f"Error resolving field request: {str(e)}",
                message_type=MessageType.notice,
            )
        )


async def handle_invite_command(
    context: ConversationContext, message: ConversationMessage, args: List[str]
) -> None:
    """Handle the invite command."""
    # Forward to the MissionManager implementation
    await MissionManager.process_invite_command(context, message, "invite")


async def handle_join_command(
    context: ConversationContext, message: ConversationMessage, args: List[str]
) -> None:
    """Handle the join command."""
    # Forward to the MissionManager implementation
    await MissionManager.process_join_command(context, message, "join")


async def handle_mission_info_command(
    context: ConversationContext, message: ConversationMessage, args: List[str]
) -> None:
    """Handle the mission-info command."""
    # Parse the command
    content = " ".join(args).strip().lower()
    
    try:
        # Determine which information to show
        info_type = content if content else "all"
        
        if info_type not in ["all", "briefing", "kb", "status", "requests"]:
            await context.send_messages(
                NewConversationMessage(
                    content="Please specify what information you want to see: `/mission-info [briefing|kb|status|requests]`",
                    message_type=MessageType.notice,
                )
            )
            return
        
        # Get the requested information
        output = []
        
        # Get mission briefing if requested
        if info_type in ["all", "briefing"]:
            briefings = await ArtifactMessenger.get_artifacts_by_type(context, MissionBriefing)
            
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
                    output.append("\n*No goals defined yet. Add goals with `/add-goal`.*")
        
        # Get mission KB if requested
        if info_type in ["all", "kb"]:
            kb_artifacts = await ArtifactMessenger.get_artifacts_by_type(context, MissionKB)
            
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
                output.append("*No knowledge base sections defined yet. Add sections with `/add-kb-section`.*")
        
        # Get mission status if requested
        if info_type in ["all", "status"]:
            status_artifacts = await ArtifactMessenger.get_artifacts_by_type(context, MissionStatus)
            
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
                output.append("*No mission status defined yet. Update status with `/update-status`.*")
        
        # Get field requests if requested
        if info_type in ["all", "requests"]:
            requests = await ArtifactMessenger.get_artifacts_by_type(context, FieldRequest)
            
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
                        }.get(str(request.priority), "🔹")
                        
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
                output.append("*No field requests created yet. Request information with `/request-info`.*")
        
        # If no data was found for any category
        if not output:
            output.append("No mission information found. Start by creating a mission briefing with `/create-briefing`.")
        
        # Send the formatted information
        await context.send_messages(
            NewConversationMessage(
                content="\n".join(output),
                message_type=MessageType.chat,
            )
        )
        
    except Exception as e:
        logger.exception(f"Error displaying mission info: {e}")
        await context.send_messages(
            NewConversationMessage(
                content=f"Error displaying mission information: {str(e)}",
                message_type=MessageType.notice,
            )
        )


async def handle_list_participants_command(
    context: ConversationContext, message: ConversationMessage, args: List[str]
) -> None:
    """Handle the list-participants command."""
    try:
        # Get links to all conversations
        links = await MissionStateManager.get_links(context)
        
        if not links.linked_conversations:
            await context.send_messages(
                NewConversationMessage(
                    content="No linked conversations found. Invite participants with the `/invite` command.",
                    message_type=MessageType.notice,
                )
            )
            return
        
        # Get participant information for all linked conversations
        output = ["## Mission Participants\n"]
        
        # First add information about this conversation
        participants = await context.get_participants()
        
        output.append("### HQ Team\n")
        for participant in participants.participants:
            if participant.id != context.assistant.id:
                output.append(f"- {participant.name}")
        
        # Add information about field participants
        field_conversations = []
        
        for conv_id, linked_conv in links.linked_conversations.items():
            if conv_id != str(context.id):
                # Skip this conversation (HQ)
                field_conversations.append({
                    "conversation_id": conv_id,
                    "user_name": linked_conv.user_name,
                    "status": linked_conv.status,
                })
        
        if field_conversations:
            output.append("\n### Field Personnel\n")
            
            for conv in field_conversations:
                status_emoji = "🟢" if conv["status"] == "active" else "⚪"
                output.append(f"- {status_emoji} {conv['user_name']}")
        else:
            output.append("\n*No field personnel yet. Invite team members with the `/invite` command.*")
        
        # Send the information
        await context.send_messages(
            NewConversationMessage(
                content="\n".join(output),
                message_type=MessageType.chat,
            )
        )
        
    except Exception as e:
        logger.exception(f"Error listing participants: {e}")
        await context.send_messages(
            NewConversationMessage(
                content=f"Error listing participants: {str(e)}",
                message_type=MessageType.notice,
            )
        )


async def handle_revoke_access_command(
    context: ConversationContext, message: ConversationMessage, args: List[str]
) -> None:
    """Handle the revoke command."""
    # Parse the command
    if not args:
        await context.send_messages(
            NewConversationMessage(
                content="Please specify a username to revoke access. Format: `/revoke username`",
                message_type=MessageType.notice,
            )
        )
        return
    
    username = args[0]
    
    try:
        # Get links to all conversations
        links = await MissionStateManager.get_links(context)
        
        if not links.linked_conversations:
            await context.send_messages(
                NewConversationMessage(
                    content="No linked conversations found.",
                    message_type=MessageType.notice,
                )
            )
            return
        
        # Find the conversation with the given username
        target_conv_id = None
        for conv_id, linked_conv in links.linked_conversations.items():
            if conv_id != str(context.id) and linked_conv.user_name.lower() == username.lower():
                target_conv_id = conv_id
                break
        
        if not target_conv_id:
            await context.send_messages(
                NewConversationMessage(
                    content=f"No participant found with username '{username}'.",
                    message_type=MessageType.notice,
                )
            )
            return
        
        # Update the status to inactive
        links.linked_conversations[target_conv_id].status = "inactive"
        
        # Save the updated links
        await MissionStateManager.save_links(context, links)
        
        # Notify the target conversation
        try:
            from .mission_manager import ConversationClientManager
            target_client = ConversationClientManager.get_conversation_client(context, target_conv_id)
            
            await target_client.send_messages(
                NewConversationMessage(
                    content="Your access to this mission has been revoked by HQ.",
                    message_type=MessageType.notice,
                )
            )
        except Exception as e:
            logger.warning(f"Could not notify revoked user: {e}")
        
        await context.send_messages(
            NewConversationMessage(
                content=f"Access revoked for {username}.",
                message_type=MessageType.chat,
            )
        )
        
    except Exception as e:
        logger.exception(f"Error revoking access: {e}")
        await context.send_messages(
            NewConversationMessage(
                content=f"Error revoking access: {str(e)}",
                message_type=MessageType.notice,
            )
        )


# Register commands in the registry

# General commands (available to all)
command_registry.register_command(
    "help",
    handle_help_command,
    "Get help with available commands",
    "/help [command]",
    "/help mission-info",
    None  # Available to all roles
)

command_registry.register_command(
    "mission-info",
    handle_mission_info_command,
    "View mission information",
    "/mission-info [briefing|kb|status|requests]",
    "/mission-info briefing",
    None  # Available to all roles
)

# Team management commands
command_registry.register_command(
    "invite",
    handle_invite_command,
    "Invite a user to join this mission",
    "/invite [username]",
    "/invite john.doe",
    ["hq"]  # Only HQ can invite
)

command_registry.register_command(
    "join",
    handle_join_command,
    "Join a mission with an invitation code",
    "/join invitation_code",
    "/join abc123:xyz456",
    None  # Available to all roles (anyone can join if they have a code)
)

command_registry.register_command(
    "list-participants",
    handle_list_participants_command,
    "List all mission participants",
    "/list-participants",
    "/list-participants",
    ["hq"]  # Only HQ can list participants
)

command_registry.register_command(
    "revoke",
    handle_revoke_access_command,
    "Revoke a participant's access to the mission",
    "/revoke username",
    "/revoke john.doe",
    ["hq"]  # Only HQ can revoke access
)

# HQ commands
command_registry.register_command(
    "create-briefing",
    handle_create_briefing_command,
    "Create a mission briefing",
    "/create-briefing Mission Name|Mission description",
    "/create-briefing Investigate Network Outage|The network in Building C went down at 3pm. We need to identify the cause and restore service.",
    ["hq"]  # Only HQ can create briefings
)

command_registry.register_command(
    "add-goal",
    handle_add_goal_command,
    "Add a goal to the mission briefing",
    "/add-goal Goal Name|Goal description|Success criterion 1;Success criterion 2",
    "/add-goal Restore Network Service|Get Building C back online|Service restored to all floors;Verified connectivity for all devices",
    ["hq"]  # Only HQ can add goals
)

command_registry.register_command(
    "add-kb-section",
    handle_add_kb_section_command,
    "Add a section to the mission knowledge base",
    "/add-kb-section Section Title|Section content",
    "/add-kb-section Network Diagram|Building C uses the following topology: [diagram details]",
    ["hq"]  # Only HQ can add KB sections
)

command_registry.register_command(
    "resolve-request",
    handle_resolve_request_command,
    "Resolve a field request",
    "/resolve-request request_id|Resolution information",
    "/resolve-request abc123|The login credentials are admin/NetworkPass2024",
    ["hq"]  # Only HQ can resolve requests
)

# Field commands
command_registry.register_command(
    "request-info",
    handle_request_info_command,
    "Request information or assistance from HQ",
    "/request-info Request Title|Request description|priority",
    "/request-info Need Server Room Access|I need the door code for the server room in Building C|high",
    ["field"]  # Only field can create requests
)

command_registry.register_command(
    "update-status",
    handle_update_status_command,
    "Update mission status and progress",
    "/update-status status|progress|message",
    "/update-status in_progress|50|Identified faulty switch on floor 3, working on replacement",
    ["field"]  # Only field can update status
)


# Main entry point for processing commands
async def process_command(context: ConversationContext, message: ConversationMessage) -> bool:
    """
    Process a command message.
    
    Args:
        context: The conversation context
        message: The command message
        
    Returns:
        True if command was processed, False otherwise
    """
    # Get the conversation's role
    from .mission_manager import MissionManager
    
    # First check conversation metadata
    conversation = await context.get_conversation()
    metadata = conversation.metadata or {}
    metadata_role = metadata.get("mission_role")
    
    # Then check the stored role from mission storage - this is the authoritative source
    stored_role = await MissionManager.get_conversation_role(context)
    stored_role_value = stored_role.value if stored_role else None
    
    # Log the roles for debugging
    logger.debug(f"Role detection in process_command - Metadata role: {metadata_role}, Stored role: {stored_role_value}")
    
    # If we have a stored role but metadata is different, use stored role (more reliable)
    if stored_role_value and metadata_role != stored_role_value:
        logger.warning(f"Role mismatch in process_command! Metadata: {metadata_role}, Storage: {stored_role_value}")
        role = stored_role_value
    else:
        # Otherwise use metadata or default to HQ
        role = metadata_role or "hq"  # Default to HQ if not set
    
    # Process the command through the registry
    return await command_registry.process_command(context, message, role)