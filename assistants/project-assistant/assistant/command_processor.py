"""
Command processor for the project assistant.

This module provides a unified framework for processing commands in the project assistant.
It defines a command registry, command handlers for both Coordinator and Team modes, and authorization
controls based on user roles.
"""

import logging
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional

from semantic_workbench_api_model.workbench_model import (
    AssistantStateEvent,
    ConversationMessage,
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from .project_data import (
    LogEntryType,
    ProjectGoal,
    RequestPriority,
    RequestStatus,
    SuccessCriterion,
)
from .project_manager import ProjectManager
from .project_storage import (
    ConversationProjectManager,
    ProjectNotifier,
    ProjectRole,
    ProjectStorage,
    ProjectStorageManager,
)

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
        return {name: cmd for name, cmd in self.commands.items() if self.is_authorized(name, role)}

    async def process_command(self, context: ConversationContext, message: ConversationMessage, role: str) -> bool:
        """
        Process a command message.

        Args:
            context: The conversation context
            message: The command message
            role: The user's role (coordinator or team)

        Returns:
            True if command was processed, False otherwise
        """
        # Split the command and extract the command name
        content = message.content.strip()
        if not content.startswith("/"):
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


async def handle_start_coordinator_command(
    context: ConversationContext, message: ConversationMessage, args: List[str]
) -> None:
    """
    Handle the start command to create a new project with this conversation as Coordinator.

    This is a setup mode command that creates a project and sets the current conversation as Coordinator.
    """
    # Get conversation to access metadata
    conversation = await context.get_conversation()
    metadata = conversation.metadata or {}

    # Check if already in a project
    project_id = await ProjectManager.get_project_id(context)
    if project_id:
        # Already in a project, show error
        await context.send_messages(
            NewConversationMessage(
                content="This conversation is already part of a project. You can use existing commands instead of setup.",
                message_type=MessageType.notice,
            )
        )
        return

    # First parse the content for project name and description
    content = message.content.strip()[len("/start") :].strip()
    project_name = "New Project"
    project_description = "A new project has been created."

    # If content provided, parse it
    if content:
        if "|" in content:
            parts = content.split("|", 1)
            project_name = parts[0].strip()
            project_description = parts[1].strip() if len(parts) > 1 else ""
        else:
            # Just a name provided
            project_name = content.strip()

    # Create a new project
    success, new_project_id = await ProjectManager.create_project(context)
    if not success or not new_project_id:
        await context.send_messages(
            NewConversationMessage(
                content="Failed to create project. Please try again.",
                message_type=MessageType.notice,
            )
        )
        return

    # Create project brief
    success, briefing = await ProjectManager.create_project_brief(
        context=context, project_name=project_name, project_description=project_description
    )

    if not success:
        await context.send_messages(
            NewConversationMessage(
                content="Failed to create project brief. Please try again.",
                message_type=MessageType.notice,
            )
        )
        return

    # Update metadata to mark setup complete and set mode to coordinator
    metadata["project_role"] = "coordinator"
    metadata["assistant_mode"] = "coordinator"
    metadata["setup_complete"] = True

    # Update conversation metadata - using None for state as the string/bool values are not allowed by the type system
    await context.send_conversation_state_event(
        AssistantStateEvent(state_id="project_role", event="updated", state=None)
    )
    await context.send_conversation_state_event(
        AssistantStateEvent(state_id="assistant_mode", event="updated", state=None)
    )
    await context.send_conversation_state_event(
        AssistantStateEvent(state_id="setup_complete", event="updated", state=None)
    )

    # Send confirmation with project ID as the invitation code
    await context.send_messages(
        NewConversationMessage(
            content=f"""# Project Created Successfully

**Project Name:** {project_name}
**Role:** Coordinator
**Project ID:** `{new_project_id}`

**IMPORTANT:** Share this Project ID with team members so they can join using `/join {new_project_id}` in their conversations.

I'm here to help you create and coordinate your project. Just tell me what you'd like to do next, or use `/help` to see available commands.

Good luck with your project!
            """,
            message_type=MessageType.chat,
        )
    )

    # Also refresh the UI inspector
    from .project_storage import ProjectStorage

    await ProjectStorage.refresh_current_ui(context)


async def handle_join_command(context: ConversationContext, message: ConversationMessage, args: List[str]) -> None:
    """
    Handle the join command to join an existing project as a team member.

    This is a setup mode command that joins an existing project as a team member using the project ID.
    """
    # Check if already in a project
    current_project_id = await ProjectManager.get_project_id(context)
    if current_project_id:
        # Already in a project, show error
        await context.send_messages(
            NewConversationMessage(
                content="This conversation is already part of a project. You can use existing commands instead of setup.",
                message_type=MessageType.notice,
            )
        )
        return

    # Get project ID from arguments
    project_id = None

    # If passed directly in command args
    if args:
        project_id = args[0]
    else:
        # Try to parse from message
        content = message.content.strip()[len("/join") :].strip()
        if content:
            project_id = content

    if not project_id:
        await context.send_messages(
            NewConversationMessage(
                content="Please provide a project ID. Usage: `/join project_id`",
                message_type=MessageType.notice,
            )
        )
        return

    # Verify the project exists
    if not ProjectStorageManager.project_exists(project_id):
        await context.send_messages(
            NewConversationMessage(
                content=f"Project with ID '{project_id}' not found. Please check the ID and try again.",
                message_type=MessageType.notice,
            )
        )
        return

    # Join the project directly (simplified approach)
    success = await ProjectManager.join_project(context, project_id, ProjectRole.TEAM)

    if not success:
        await context.send_messages(
            NewConversationMessage(
                content="Failed to join project. Please try again.",
                message_type=MessageType.notice,
            )
        )
        return

    # Get conversation to access metadata
    conversation = await context.get_conversation()
    metadata = conversation.metadata or {}

    # Update metadata to mark setup complete and set mode to team
    metadata["project_role"] = "team"
    metadata["assistant_mode"] = "team"
    metadata["setup_complete"] = True

    # Update conversation metadata - using None for state as the string/bool values are not allowed by the type system
    await context.send_conversation_state_event(
        AssistantStateEvent(state_id="project_role", event="updated", state=None)
    )
    await context.send_conversation_state_event(
        AssistantStateEvent(state_id="assistant_mode", event="updated", state=None)
    )
    await context.send_conversation_state_event(
        AssistantStateEvent(state_id="setup_complete", event="updated", state=None)
    )

    # Get project name and ID for the welcome message
    briefing = await ProjectManager.get_project_brief(context)
    project_name = briefing.project_name if briefing else "Project"
    project_id = await ProjectManager.get_project_id(context)

    # Send confirmation
    await context.send_messages(
        NewConversationMessage(
            content=f"""# Joined Project Successfully

**Project Name:** {project_name}
**Project ID:** `{project_id}`
**Role:** Team

You are now connected to the Coordinator and can see all project information. You can use Team commands to:
- Get project information with `/get-project-info`
- Request information from the Coordinator with `/request-info`
- Update project status with `/update-status`
- Get help with other commands using `/help`

Welcome to the project!
            """,
            message_type=MessageType.chat,
        )
    )

    # Also refresh the UI inspector
    from .project_storage import ProjectStorage

    await ProjectStorage.refresh_current_ui(context)


async def handle_help_command(context: ConversationContext, message: ConversationMessage, args: List[str]) -> None:
    """Handle the help command."""
    # Get the conversation's role
    from .project_storage import ConversationProjectManager

    # First check conversation metadata
    conversation = await context.get_conversation()
    metadata = conversation.metadata or {}
    setup_complete = metadata.get("setup_complete", False)
    assistant_mode = metadata.get("assistant_mode", "setup")
    metadata_role = metadata.get("project_role")

    # First check if project ID exists - if it does, setup should be considered complete
    project_id = await ProjectManager.get_project_id(context)
    if project_id:
        # If we have a project ID, we should never show the setup instructions
        setup_complete = True

        # If metadata doesn't reflect this, try to get actual role
        if not metadata.get("setup_complete", False):
            role = await ConversationProjectManager.get_conversation_role(context)
            if role:
                metadata_role = role.value
            else:
                # Default to team mode if we can't determine role
                metadata_role = "team"

    # Special handling for setup mode - only if we truly have no project
    if not setup_complete and assistant_mode == "setup" and not project_id:
        # If a specific command is specified, show detailed help for that command
        if args:
            command_name = args[0]
            if command_name.startswith("/"):
                command_name = command_name[1:]  # Remove the '/' prefix

            # For setup mode, only show help for setup commands
            setup_commands = ["start-coordinator", "join", "help"]

            if command_name in setup_commands:
                help_info = command_registry.get_command_help(command_name)
                if help_info:
                    await context.send_messages(
                        NewConversationMessage(
                            content=f"""## Help: /{command_name}

{help_info["description"]}

**Usage:** {help_info["usage"]}

**Example:** {help_info["example"]}
""",
                            message_type=MessageType.chat,
                        )
                    )
                    return

            # If not a setup command, show generic message
            await context.send_messages(
                NewConversationMessage(
                    content=f"The /{command_name} command is not available in setup mode. Please first use `/start-coordinator` or `/join` to establish your role.",
                    message_type=MessageType.notice,
                )
            )
            return

        # Show setup-specific help
        help_text = """## Project Assistant

This assistant is automatically set up to help you with your project:

- As a Coordinator: This conversation is your personal conversation for managing the project
- As a Team Member: This conversation is for collaborating on the project with others

No setup commands needed! You're already good to go.

Type `/help` to see all available commands for your role.
"""

        await context.send_messages(
            NewConversationMessage(
                content=help_text,
                message_type=MessageType.chat,
            )
        )
        return

    # Normal (non-setup) help processing
    # Then check the stored role from project storage - this is the authoritative source
    stored_role = await ConversationProjectManager.get_conversation_role(context)
    stored_role_value = stored_role.value if stored_role else None

    # Log the roles for debugging
    logger.debug(f"Role detection in help command - Metadata role: {metadata_role}, Stored role: {stored_role_value}")

    # If we have a stored role but metadata is different, use stored role (more reliable)
    if stored_role_value and metadata_role != stored_role_value:
        logger.warning(f"Role mismatch in help command! Metadata: {metadata_role}, Storage: {stored_role_value}")
        role = stored_role_value
    else:
        # Otherwise use metadata or default to coordinator
        role = metadata_role or "coordinator"  # Default to coordinator if not set

    # If a specific command is specified, show detailed help for that command
    if args:
        command_name = args[0]
        if command_name.startswith("/"):
            command_name = command_name[1:]  # Remove the '/' prefix

        help_info = command_registry.get_command_help(command_name)

        if help_info and command_registry.is_authorized(command_name, role):
            await context.send_messages(
                NewConversationMessage(
                    content=f"""## Help: /{command_name}

{help_info["description"]}

**Usage:** {help_info["usage"]}

**Example:** {help_info["example"]}
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
    if role == "coordinator":
        help_text = "## Assistant Commands (Coordinator Mode)\n\n"
    else:
        help_text = "## Assistant Commands (Team Mode)\n\n"

    # Group commands by category
    project_commands = []
    whiteboard_commands = []
    request_commands = []
    team_commands = []
    status_commands = []
    info_commands = []

    for name, cmd in available_commands.items():
        command_entry = f"- `/{name}`: {cmd['description']}"

        if "create-brief" in name or "add-goal" in name:
            project_commands.append(command_entry)
        elif "whiteboard" in name:
            whiteboard_commands.append(command_entry)
        elif "request" in name:
            request_commands.append(command_entry)
        elif "invite" in name or "join" in name or "list-participants" in name:
            team_commands.append(command_entry)
        elif "status" in name or "update" in name:
            status_commands.append(command_entry)
        else:
            info_commands.append(command_entry)

    # Add sections to help text if they have commands
    if project_commands:
        help_text += "### Project Configuration\n" + "\n".join(project_commands) + "\n\n"

    if whiteboard_commands:
        help_text += "### Whiteboard Management\n" + "\n".join(whiteboard_commands) + "\n\n"

    if team_commands:
        help_text += "### Team Management\n" + "\n".join(team_commands) + "\n\n"

    if request_commands:
        help_text += "### Information Request Management\n" + "\n".join(request_commands) + "\n\n"

    if status_commands:
        help_text += "### Status Management\n" + "\n".join(status_commands) + "\n\n"

    if info_commands:
        help_text += "### Information\n" + "\n".join(info_commands) + "\n\n"

    # Add role-specific guidance
    if role == "coordinator":
        help_text += (
            "As a Coordinator, you are responsible for defining the project and responding to team member requests."
        )
    else:
        help_text += "As a Team member, you can access project information, request information, and report progress on project goals."

    await context.send_messages(
        NewConversationMessage(
            content=help_text,
            message_type=MessageType.chat,
        )
    )


async def handle_create_brief_command(
    context: ConversationContext, message: ConversationMessage, args: List[str]
) -> None:
    """Handle the create-brief command."""
    # Parse the command
    content = message.content.strip()[len("/create-brief") :].strip()

    if not content or "|" not in content:
        await context.send_messages(
            NewConversationMessage(
                content="Please provide a project name and description in the format: `/create-brief Project Name|Project description here`",
                message_type=MessageType.notice,
            )
        )
        return

    # Extract project name and description
    try:
        project_name, project_description = content.split("|", 1)
        project_name = project_name.strip()
        project_description = project_description.strip()

        if not project_name or not project_description:
            raise ValueError("Both project name and description are required")

        # Create a new project
        success, project_id = await ProjectManager.create_project(context)
        if not success:
            raise ValueError("Failed to create project")

        # Create the project brief without sending a notification (we'll send our own)
        success, briefing = await ProjectManager.create_project_brief(
            context, project_name, project_description, send_notification=False
        )

        if success and briefing:
            await context.send_messages(
                NewConversationMessage(
                    content=f"Project brief '{project_name}' created successfully.",
                    message_type=MessageType.chat,
                )
            )
        else:
            await context.send_messages(
                NewConversationMessage(
                    content="Failed to create project brief. Please try again.",
                    message_type=MessageType.notice,
                )
            )
    except Exception as e:
        logger.exception(f"Error creating project brief: {e}")
        await context.send_messages(
            NewConversationMessage(
                content=f"Error creating project brief: {str(e)}",
                message_type=MessageType.notice,
            )
        )


async def handle_add_goal_command(context: ConversationContext, message: ConversationMessage, args: List[str]) -> None:
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

        # Get project ID
        project_id = await ConversationProjectManager.get_associated_project_id(context)
        if not project_id:
            await context.send_messages(
                NewConversationMessage(
                    content="You are not associated with a project. Please create one first with `/create-brief`.",
                    message_type=MessageType.notice,
                )
            )
            return

        # Get existing project brief
        briefing = await ProjectManager.get_project_brief(context)
        if not briefing:
            await context.send_messages(
                NewConversationMessage(
                    content="No project brief found. Please create one first with `/create-brief`.",
                    message_type=MessageType.notice,
                )
            )
            return

        # Create success criterion objects
        criterion_objects = [SuccessCriterion(description=criterion) for criterion in success_criteria]

        # Create the goal
        goal = ProjectGoal(
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
        ProjectStorage.write_project_brief(project_id, briefing)
        success = True

        if success:
            # Log the update
            await ProjectStorage.log_project_event(
                context=context,
                project_id=project_id,
                entry_type=LogEntryType.BRIEFING_UPDATED.value,
                message=f"Added goal: {goal_name}",
                related_entity_id=goal.id,
            )

            # Notify all linked conversations about the update
            await ProjectNotifier.notify_project_update(
                context=context,
                project_id=project_id,
                update_type="briefing",
                message=f"Goal added to project: {goal_name}",
            )

            # Build success criteria message
            criteria_msg = ""
            if success_criteria:
                criteria_list = "\n".join([f"- {c}" for c in success_criteria])
                criteria_msg = f"\n\nSuccess Criteria:\n{criteria_list}"

            await context.send_messages(
                NewConversationMessage(
                    content=f"Goal '{goal_name}' added to project brief successfully.{criteria_msg}",
                    message_type=MessageType.chat,
                )
            )
        else:
            await context.send_messages(
                NewConversationMessage(
                    content="Failed to update project brief with new goal. Please try again.",
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


# Whiteboard auto-update separator


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

        # Create the information request
        success, request = await ProjectManager.create_information_request(
            context=context, title=title, description=description, priority=priority
        )

        if success and request:
            await context.send_messages(
                NewConversationMessage(
                    content=f"Information request '{title}' created successfully with {priority_str} priority. The Coordinator has been notified and will respond to your request.",
                    message_type=MessageType.chat,
                )
            )
        else:
            await context.send_messages(
                NewConversationMessage(
                    content="Failed to create information request. Please try again.",
                    message_type=MessageType.notice,
                )
            )
    except Exception as e:
        logger.exception(f"Error creating information request: {e}")
        await context.send_messages(
            NewConversationMessage(
                content=f"Error creating information request: {str(e)}",
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

        # Update the project status
        success, status_obj = await ProjectManager.update_project_state(
            context=context, state=status, status_message=status_message
        )

        if success and status_obj:
            # Format progress as percentage if available
            progress_text = f" ({progress}% complete)" if progress is not None else ""

            await context.send_messages(
                NewConversationMessage(
                    content=f"Project status updated to '{status}'{progress_text}. All project participants will see this update.",
                    message_type=MessageType.chat,
                )
            )
        else:
            await context.send_messages(
                NewConversationMessage(
                    content="Failed to update project status. Please try again.",
                    message_type=MessageType.notice,
                )
            )
    except Exception as e:
        logger.exception(f"Error updating project status: {e}")
        await context.send_messages(
            NewConversationMessage(
                content=f"Error updating project status: {str(e)}",
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

        # Show all information requests if the user doesn't know the ID
        if request_id.lower() == "list":
            await context.send_messages(
                NewConversationMessage(
                    content="Here are the active information requests:",
                    message_type=MessageType.notice,
                )
            )

            # Get information requests
            requests = await ProjectManager.get_information_requests(context)

            # Filter for active requests
            active_requests = [r for r in requests if r.status != RequestStatus.RESOLVED]

            if active_requests:
                request_list = ["## Active Information Requests\n"]

                for request in active_requests:
                    request_list.append(f"**ID**: `{request.request_id}`")
                    request_list.append(f"**Title**: {request.title}")
                    request_list.append(f"**Priority**: {request.priority.value}")
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
                        content="No active information requests found.",
                        message_type=MessageType.notice,
                    )
                )
            return

        # Resolve the information request
        success, info_request = await ProjectManager.resolve_information_request(
            context=context, request_id=request_id, resolution=resolution
        )

        if success and info_request:
            await context.send_messages(
                NewConversationMessage(
                    content=f"Information request '{info_request.title}' has been resolved. The Team has been notified.",
                    message_type=MessageType.chat,
                )
            )
        else:
            await context.send_messages(
                NewConversationMessage(
                    content="Failed to resolve the information request. Make sure the request ID is correct and the request is not already resolved.",
                    message_type=MessageType.notice,
                )
            )

            # Suggest listing all requests to help the user
            await context.send_messages(
                NewConversationMessage(
                    content="Use `/resolve-request list|` to view all information requests and their IDs.",
                    message_type=MessageType.notice,
                )
            )
    except Exception as e:
        logger.exception(f"Error resolving information request: {e}")
        await context.send_messages(
            NewConversationMessage(
                content=f"Error resolving information request: {str(e)}",
                message_type=MessageType.notice,
            )
        )


async def handle_project_info_command(
    context: ConversationContext, message: ConversationMessage, args: List[str]
) -> None:
    """Handle the project-info command."""
    # Parse the command
    content = " ".join(args).strip().lower()

    try:
        # Determine which information to show
        info_type = content if content else "all"

        if info_type not in ["all", "brief", "whiteboard", "status", "requests"]:
            await context.send_messages(
                NewConversationMessage(
                    content="Please specify what information you want to see: `/project-info [brief|whiteboard|status|requests]`",
                    message_type=MessageType.notice,
                )
            )
            return

        # Get the requested information
        output = []

        # Always show project ID at the top for easy access
        project_id = await ProjectManager.get_project_id(context)
        if project_id:
            # Check if Coordinator or Team
            role = await ProjectManager.get_project_role(context)
            if role == ProjectRole.COORDINATOR:
                # For Coordinator, make it prominent with instructions
                output.append(f"## Project ID: `{project_id}`")
                output.append(f"_Share this ID with team members so they can join using_ `/join {project_id}`\n")
            else:
                # For Team, just show the ID
                output.append(f"## Project ID: `{project_id}`\n")

        # Get project brief if requested
        if info_type in ["all", "brief"]:
            briefing = await ProjectManager.get_project_brief(context)

            if briefing:
                # Format briefing information
                output.append(f"## Project Brief: {briefing.project_name}")
                output.append(f"\n{briefing.project_description}\n")

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

        # Get project whiteboard if requested
        if info_type in ["all", "whiteboard"]:
            whiteboard = await ProjectManager.get_project_whiteboard(context)

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
                output.append(
                    "*No whiteboard content available yet. Content will be automatically generated as the project progresses.*"
                )

        # Get project status if requested
        if info_type in ["all", "status"]:
            project_info = await ProjectManager.get_project_info(context)

            if project_info:
                output.append("\n## Project Dashboard\n")
                output.append(f"**Current Status**: {project_info.state.value}")

                if project_info.status_message:
                    output.append(f"**Status Message**: {project_info.status_message}")

                # Success criteria status can be calculated from the brief if needed later
            elif info_type == "status":
                output.append("\n## Project Dashboard\n")
                output.append("*No project status defined yet. Update status with `/update-status`.*")

        # Get information requests if requested
        if info_type in ["all", "requests"]:
            requests = await ProjectManager.get_information_requests(context)

            if requests:
                output.append("\n## Information Requests\n")

                # Group requests by status
                active_requests = [r for r in requests if r.status != RequestStatus.RESOLVED]
                resolved_requests = [r for r in requests if r.status == RequestStatus.RESOLVED]

                if active_requests:
                    output.append("### Active Requests\n")

                    for request in active_requests:
                        priority_marker = {
                            RequestPriority.LOW.value: "🔹",
                            RequestPriority.MEDIUM.value: "🔶",
                            RequestPriority.HIGH.value: "🔴",
                            RequestPriority.CRITICAL.value: "⚠️",
                        }.get(request.priority.value, "🔹")

                        # Include request ID for easy reference when resolving
                        output.append(f"{priority_marker} **{request.title}** ({request.status.value})")
                        output.append(f"  ID: `{request.request_id}`")
                        output.append(f"  {request.description}")

                        if request.updates:
                            last_update = request.updates[-1]
                            output.append(f"  *Last update: {last_update.get('message', '')}*")

                        output.append("")

                if resolved_requests and info_type == "requests":
                    output.append("### Resolved Requests\n")

                    for request in resolved_requests[:5]:  # Show only the 5 most recent
                        output.append(f"✅ **{request.title}** ({request.status.value})")
                        output.append(f"  ID: `{request.request_id}`")

                        if request.resolution:
                            output.append(f"  Resolution: {request.resolution}")

                        output.append("")
            elif info_type == "requests":
                output.append("\n## Information Requests\n")
                output.append("*No information requests created yet. Request information with `/request-info`.*")

        # If no data was found for any category
        if not output:
            output.append("No project information found. Start by creating a project brief with `/create-brief`.")

        # Send the formatted information
        await context.send_messages(
            NewConversationMessage(
                content="\n".join(output),
                message_type=MessageType.chat,
            )
        )

    except Exception as e:
        logger.exception(f"Error displaying project info: {e}")
        await context.send_messages(
            NewConversationMessage(
                content=f"Error displaying project information: {str(e)}",
                message_type=MessageType.notice,
            )
        )


async def handle_list_participants_command(
    context: ConversationContext, message: ConversationMessage, args: List[str]
) -> None:
    """Handle the list-participants command."""
    try:
        # Get project ID
        project_id = await ConversationProjectManager.get_associated_project_id(context)
        if not project_id:
            await context.send_messages(
                NewConversationMessage(
                    content="You are not associated with a project.",
                    message_type=MessageType.notice,
                )
            )
            return

        # Get all linked conversations
        linked_conversation_ids = await ConversationProjectManager.get_linked_conversations(context)

        if not linked_conversation_ids:
            await context.send_messages(
                NewConversationMessage(
                    content="No linked conversations found. Invite participants with the `/invite` command.",
                    message_type=MessageType.notice,
                )
            )
            return

        # Get participant information for all linked conversations
        output = ["## Project Participants\n"]

        # First add information about this conversation
        participants = await context.get_participants()

        output.append("### Coordinator Team\n")
        for participant in participants.participants:
            if participant.id != context.assistant.id:
                output.append(f"- {participant.name}")

        # In the simplified implementation, we don't have detail about the linked conversations
        # For a more complete implementation, we would need to get information
        # about each linked conversation

        # For now, just report that we have no other team members
        output.append("\n*No team members yet. Invite team members with the `/invite` command.*")

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


# File synchronization command handler
async def handle_sync_files_command(
    context: ConversationContext, message: ConversationMessage, args: List[str]
) -> None:
    """
    Handle the sync-files command which synchronizes shared files from Coordinator to Team.

    This is primarily for Team members to explicitly request a file sync
    if they suspect files are out of sync or missing.
    """
    try:
        # Get project ID
        project_id = await ProjectManager.get_project_id(context)
        if not project_id:
            await context.send_messages(
                NewConversationMessage(
                    content="You are not associated with a project. Please join a project first.",
                    message_type=MessageType.notice,
                )
            )
            return

        # Import the file manager
        from .project_files import ProjectFileManager

        # Start sync with a simple message
        await context.send_messages(
            NewConversationMessage(
                content="Synchronizing files from project...",
                message_type=MessageType.notice,
            )
        )

        # Perform synchronization directly - this handles all error messaging
        await ProjectFileManager.synchronize_files_to_team_conversation(context=context, project_id=project_id)

    except Exception as e:
        logger.exception(f"Error synchronizing files: {e}")
        await context.send_messages(
            NewConversationMessage(
                content=f"Error synchronizing files: {str(e)}",
                message_type=MessageType.notice,
            )
        )


# Setup mode commands are no longer needed - they're handled automatically

# General commands (available to all)
command_registry.register_command(
    "help",
    handle_help_command,
    "Get help with available commands",
    "/help [command]",
    "/help project-info",
    None,  # Available to all roles
)

command_registry.register_command(
    "project-info",
    handle_project_info_command,
    "View project information",
    "/project-info [brief|whiteboard|status|requests]",
    "/project-info brief",
    None,  # Available to all roles
)

# Team management commands
# Note: Manual project joining with /join is no longer needed - users just click the share URL

command_registry.register_command(
    "list-participants",
    handle_list_participants_command,
    "List all project participants",
    "/list-participants",
    "/list-participants",
    ["coordinator"],  # Only Coordinator can list participants
)


# Coordinator commands
command_registry.register_command(
    "create-brief",
    handle_create_brief_command,
    "Create a project brief",
    "/create-brief Project Name|Project description",
    "/create-brief Website Redesign|We need to modernize our company website to improve user experience and conversions.",
    ["coordinator"],  # Only Coordinator can create briefs
)

command_registry.register_command(
    "add-goal",
    handle_add_goal_command,
    "Add a goal to the project brief",
    "/add-goal Goal Name|Goal description|Success criterion 1;Success criterion 2",
    "/add-goal Redesign Homepage|Create a new responsive homepage|Design approved by stakeholders;Mobile compatibility verified",
    ["coordinator"],  # Only Coordinator can add goals
)


command_registry.register_command(
    "resolve-request",
    handle_resolve_request_command,
    "Resolve an information request",
    "/resolve-request request_id|Resolution information",
    "/resolve-request abc123|The API documentation can be found at docs.example.com/api",
    ["coordinator"],  # Only Coordinator can resolve requests
)

# Team commands
command_registry.register_command(
    "request-info",
    handle_request_info_command,
    "Request information or assistance from the Coordinator",
    "/request-info Request Title|Request description|priority",
    "/request-info Need API Documentation|I need access to the API documentation for integration|high",
    ["team"],  # Only team can create requests
)

command_registry.register_command(
    "update-status",
    handle_update_status_command,
    "Update project status and progress",
    "/update-status status|progress|message",
    "/update-status in_progress|50|Completed homepage wireframes, working on mobile design",
    ["team"],  # Only team can update status
)

# File synchronization command (primarily for team members)
command_registry.register_command(
    "sync-files",
    handle_sync_files_command,
    "Synchronize shared files from the project to this conversation",
    "/sync-files",
    "/sync-files",
    ["team"],  # Primarily for team members
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
    from .project_storage import ConversationProjectManager

    # First check conversation metadata
    conversation = await context.get_conversation()
    metadata = conversation.metadata or {}

    # Check if setup is complete
    setup_complete = metadata.get("setup_complete", False)

    # If not set in local metadata, try to get it from the state API via the state events
    if not setup_complete:
        try:
            # Get state directly from conversation state
            from .state_inspector import ProjectInspectorStateProvider

            inspector = ProjectInspectorStateProvider(None)
            state_data = await inspector.get(context)

            if state_data and state_data.data and state_data.data.get("content"):
                content = state_data.data.get("content", "")
                # Check if content indicates we're in Coordinator or Team mode (not in setup mode)
                if "Role: Coordinator" in content or "Role: Team" in content:
                    setup_complete = True
                    # Extract role from content
                    if "Role: Coordinator" in content:
                        metadata["project_role"] = "coordinator"
                        metadata["assistant_mode"] = "coordinator"
                    else:
                        metadata["project_role"] = "team"
                        metadata["assistant_mode"] = "team"
                    metadata["setup_complete"] = True

                    logger.info(f"Found role in state inspector: {metadata['project_role']}")
        except Exception as e:
            logger.exception(f"Error getting role from state inspector: {e}")

    assistant_mode = metadata.get("assistant_mode", "setup")

    # Get the command name and arguments
    if message.message_type != MessageType.command:
        return False

    command_name = message.command_name
    if command_name.startswith("/"):
        command_name = command_name[1:]  # Remove the '/' prefix
    args = message.command_args.split() if message.command_args else []

    # Special handling for setup mode
    if not setup_complete and assistant_mode == "setup":
        # First check if project ID exists - if it does, setup should be complete regardless
        project_id = await ProjectManager.get_project_id(context)
        if project_id:
            logger.info(f"Found project ID {project_id}, but setup_complete is False. This is inconsistent.")
            # We have a project ID but setup_complete is False - this is inconsistent
            # Force setup to be considered complete since we have a project
            setup_complete = True
            metadata["setup_complete"] = True
            # Try to get role - default to team if we can't determine
            role = await ConversationProjectManager.get_conversation_role(context)
            if role:
                metadata["project_role"] = role.value
                metadata["assistant_mode"] = role.value
                logger.info(f"Fixed role based on storage: {role.value}")
            else:
                # Default to team mode if we can't determine
                metadata["project_role"] = "team"
                metadata["assistant_mode"] = "team"
                logger.info("Could not determine role, defaulting to team mode")

            # Update conversation metadata to fix this inconsistency for future commands
            await context.send_conversation_state_event(
                AssistantStateEvent(state_id="setup_complete", event="updated", state=None)
            )
            await context.send_conversation_state_event(
                AssistantStateEvent(state_id="project_role", event="updated", state=None)
            )
            await context.send_conversation_state_event(
                AssistantStateEvent(state_id="assistant_mode", event="updated", state=None)
            )

            # Continue to normal command processing below
            logger.info(f"Fixed inconsistent state, processing command {command_name} normally")
        else:
            # Only truly in setup mode if we don't have a project ID
            # Always allow these commands in setup mode
            setup_commands = ["start", "join", "help"]

            if command_name in setup_commands:
                # If the command is a setup command, process it
                if command_name == "help":
                    await handle_help_command(context, message, args)
                    return True
                elif command_name in command_registry.commands:
                    await command_registry.commands[command_name]["handler"](context, message, args)
                    return True
            else:
                # Show message for commands that require an active project
                await context.send_messages(
                    NewConversationMessage(
                        content=(
                            "**Project not detected**\n\n"
                            "Your project is still being set up. Please wait a moment and try again.\n\n"
                            "If this persists, please report this issue - this should happen automatically."
                        ),
                        message_type=MessageType.notice,
                    )
                )
                return True

    # Standard command processing for non-setup mode
    metadata_role = metadata.get("project_role")

    # Then check the stored role from project storage - this is the authoritative source
    stored_role = await ConversationProjectManager.get_conversation_role(context)
    stored_role_value = stored_role.value if stored_role else None

    # Log the roles for debugging
    logger.debug(
        f"Role detection in process_command - Metadata role: {metadata_role}, Stored role: {stored_role_value}"
    )

    # If we have a stored role but metadata is different, use stored role (more reliable)
    if stored_role_value and metadata_role != stored_role_value:
        logger.warning(f"Role mismatch in process_command! Metadata: {metadata_role}, Storage: {stored_role_value}")
        role = stored_role_value
    else:
        # Otherwise use metadata or default to coordinator
        role = metadata_role or "coordinator"  # Default to coordinator if not set

    # Process the command through the registry
    return await command_registry.process_command(context, message, role)
