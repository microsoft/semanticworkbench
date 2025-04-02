"""
Command processor for the mission assistant.

This module provides a unified framework for processing commands in the mission assistant.
It defines a command registry, command handlers for both HQ and Field modes, and authorization
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


from .mission_data import (
    KBSection,
    LogEntryType,
    MissionGoal,
    MissionKB,
    RequestPriority,
    RequestStatus,
    SuccessCriterion,
)
from .mission_manager import MissionManager
from .mission_storage import (
    ConversationMissionManager,
    MissionNotifier,
    MissionStorage,
    MissionStorageManager,
    MissionRole,
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
            role: The user's role (hq or field)

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


async def handle_start_hq_command(context: ConversationContext, message: ConversationMessage, args: List[str]) -> None:
    """
    Handle the start-hq command to create a new mission with this conversation as HQ.

    This is a setup mode command that creates a mission and sets the current conversation as HQ.
    """
    # Get conversation to access metadata
    conversation = await context.get_conversation()
    metadata = conversation.metadata or {}

    # Check if already in a mission
    mission_id = await MissionManager.get_mission_id(context)
    if mission_id:
        # Already in a mission, show error
        await context.send_messages(
            NewConversationMessage(
                content="This conversation is already part of a mission. You can use existing commands instead of setup.",
                message_type=MessageType.notice,
            )
        )
        return

    # First parse the content for mission name and description
    content = message.content.strip()[len("/start-hq") :].strip()
    mission_name = "New Mission"
    mission_description = "A new mission has been created."

    # If content provided, parse it
    if content:
        if "|" in content:
            parts = content.split("|", 1)
            mission_name = parts[0].strip()
            mission_description = parts[1].strip() if len(parts) > 1 else ""
        else:
            # Just a name provided
            mission_name = content.strip()

    # Create a new mission
    success, new_mission_id = await MissionManager.create_mission(context)
    if not success or not new_mission_id:
        await context.send_messages(
            NewConversationMessage(
                content="Failed to create mission. Please try again.",
                message_type=MessageType.notice,
            )
        )
        return

    # Create mission briefing
    success, briefing = await MissionManager.create_mission_briefing(
        context=context, mission_name=mission_name, mission_description=mission_description
    )

    if not success:
        await context.send_messages(
            NewConversationMessage(
                content="Failed to create mission briefing. Please try again.",
                message_type=MessageType.notice,
            )
        )
        return

    # Update metadata to mark setup complete and set mode to HQ
    metadata["mission_role"] = "hq"
    metadata["assistant_mode"] = "hq"
    metadata["setup_complete"] = True

    # Update conversation metadata - using None for state as the string/bool values are not allowed by the type system
    await context.send_conversation_state_event(
        AssistantStateEvent(state_id="mission_role", event="updated", state=None)
    )
    await context.send_conversation_state_event(
        AssistantStateEvent(state_id="assistant_mode", event="updated", state=None)
    )
    await context.send_conversation_state_event(
        AssistantStateEvent(state_id="setup_complete", event="updated", state=None)
    )

    # Send confirmation with mission ID as the invitation code
    await context.send_messages(
        NewConversationMessage(
            content=f"""# Mission Created Successfully
            
**Mission Name:** {mission_name}
**Role:** HQ
**Mission ID:** `{new_mission_id}`

**IMPORTANT:** Share this Mission ID with field personnel so they can join using `/join {new_mission_id}` in their conversations.

You can now use HQ commands to:
- Define mission goals with `/add-goal`
- Add information to the knowledge base with `/add-kb-section`
- Get help with other commands using `/help`

Good luck with your mission!
            """,
            message_type=MessageType.chat,
        )
    )

    # Also refresh the UI inspector
    from .mission_storage import MissionStorage

    await MissionStorage.refresh_current_ui(context)


async def handle_join_command(context: ConversationContext, message: ConversationMessage, args: List[str]) -> None:
    """
    Handle the join command to join an existing mission as a field agent.

    This is a setup mode command that joins an existing mission as a field agent using the mission ID.
    """
    # Check if already in a mission
    current_mission_id = await MissionManager.get_mission_id(context)
    if current_mission_id:
        # Already in a mission, show error
        await context.send_messages(
            NewConversationMessage(
                content="This conversation is already part of a mission. You can use existing commands instead of setup.",
                message_type=MessageType.notice,
            )
        )
        return

    # Get mission ID from arguments
    mission_id = None

    # If passed directly in command args
    if args:
        mission_id = args[0]
    else:
        # Try to parse from message
        content = message.content.strip()[len("/join") :].strip()
        if content:
            mission_id = content

    if not mission_id:
        await context.send_messages(
            NewConversationMessage(
                content="Please provide a mission ID. Usage: `/join mission_id`",
                message_type=MessageType.notice,
            )
        )
        return

    # Verify the mission exists
    if not MissionStorageManager.mission_exists(mission_id):
        await context.send_messages(
            NewConversationMessage(
                content=f"Mission with ID '{mission_id}' not found. Please check the ID and try again.",
                message_type=MessageType.notice,
            )
        )
        return
        
    # Join the mission directly (simplified approach)
    success = await MissionManager.join_mission(context, mission_id, MissionRole.FIELD)

    if not success:
        await context.send_messages(
            NewConversationMessage(
                content="Failed to join mission. Please try again.",
                message_type=MessageType.notice,
            )
        )
        return

    # Get conversation to access metadata
    conversation = await context.get_conversation()
    metadata = conversation.metadata or {}

    # Update metadata to mark setup complete and set mode to field
    metadata["mission_role"] = "field"
    metadata["assistant_mode"] = "field"
    metadata["setup_complete"] = True

    # Update conversation metadata - using None for state as the string/bool values are not allowed by the type system
    await context.send_conversation_state_event(
        AssistantStateEvent(state_id="mission_role", event="updated", state=None)
    )
    await context.send_conversation_state_event(
        AssistantStateEvent(state_id="assistant_mode", event="updated", state=None)
    )
    await context.send_conversation_state_event(
        AssistantStateEvent(state_id="setup_complete", event="updated", state=None)
    )

    # Get mission name and ID for the welcome message
    briefing = await MissionManager.get_mission_briefing(context)
    mission_name = briefing.mission_name if briefing else "Mission"
    mission_id = await MissionManager.get_mission_id(context)

    # Send confirmation
    await context.send_messages(
        NewConversationMessage(
            content=f"""# Joined Mission Successfully
            
**Mission Name:** {mission_name}
**Mission ID:** `{mission_id}`
**Role:** Field

You are now connected to HQ and can see all mission information. You can use Field commands to:
- Get mission information with `/get-mission-info`
- Request information from HQ with `/request-info`
- Update mission status with `/update-status`
- Get help with other commands using `/help`

Welcome to the mission!
            """,
            message_type=MessageType.chat,
        )
    )

    # Also refresh the UI inspector
    from .mission_storage import MissionStorage

    await MissionStorage.refresh_current_ui(context)


async def handle_help_command(context: ConversationContext, message: ConversationMessage, args: List[str]) -> None:
    """Handle the help command."""
    # Get the conversation's role
    from .mission_storage import ConversationMissionManager

    # First check conversation metadata
    conversation = await context.get_conversation()
    metadata = conversation.metadata or {}
    setup_complete = metadata.get("setup_complete", False)
    assistant_mode = metadata.get("assistant_mode", "setup")
    metadata_role = metadata.get("mission_role")

    # Special handling for setup mode
    if not setup_complete and assistant_mode == "setup":
        # If a specific command is specified, show detailed help for that command
        if args:
            command_name = args[0]
            if command_name.startswith("/"):
                command_name = command_name[1:]  # Remove the '/' prefix

            # For setup mode, only show help for setup commands
            setup_commands = ["start-hq", "join", "help"]

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
                    content=f"The /{command_name} command is not available in setup mode. Please first use `/start-hq` or `/join` to establish your role.",
                    message_type=MessageType.notice,
                )
            )
            return

        # Show setup-specific help
        help_text = """## Mission Assistant Setup

This assistant is in setup mode. You need to establish your role before proceeding:

### Available Commands

- `/start-hq [Mission Name|Mission description]`: Create a new mission with this conversation as HQ
- `/join mission_id`: Join an existing mission as a Field agent
- `/help [command]`: Show help for a specific command

Please use one of these commands to get started. The recommended workflow is:

1. One conversation uses `/start-hq` to create the mission and become HQ
2. HQ shares the mission ID (automatically displayed after creation)
3. Field personnel use `/join` with the mission ID in their conversations

Once setup is complete, you will have access to all mission commands appropriate for your role.
"""

        await context.send_messages(
            NewConversationMessage(
                content=help_text,
                message_type=MessageType.chat,
            )
        )
        return

    # Normal (non-setup) help processing
    # Then check the stored role from mission storage - this is the authoritative source
    stored_role = await ConversationMissionManager.get_conversation_role(context)
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

        # Create a new mission
        success, mission_id = await MissionManager.create_mission(context)
        if not success:
            raise ValueError("Failed to create mission")

        # Create the mission briefing
        success, briefing = await MissionManager.create_mission_briefing(context, mission_name, mission_description)

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

        # Get mission ID
        mission_id = await ConversationMissionManager.get_conversation_mission(context)
        if not mission_id:
            await context.send_messages(
                NewConversationMessage(
                    content="You are not associated with a mission. Please create one first with `/create-mission`.",
                    message_type=MessageType.notice,
                )
            )
            return

        # Get existing mission briefing
        briefing = await MissionManager.get_mission_briefing(context)
        if not briefing:
            await context.send_messages(
                NewConversationMessage(
                    content="No mission briefing found. Please create one first with `/create-mission`.",
                    message_type=MessageType.notice,
                )
            )
            return

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
        MissionStorage.write_mission_briefing(mission_id, briefing)
        success = True

        if success:
            # Log the update
            await MissionStorage.log_mission_event(
                context=context,
                mission_id=mission_id,
                entry_type=LogEntryType.BRIEFING_UPDATED.value,
                message=f"Added goal: {goal_name}",
                related_entity_id=goal.id,
            )

            # Notify all linked conversations about the update
            await MissionNotifier.notify_mission_update(
                context=context,
                mission_id=mission_id,
                update_type="briefing",
                message=f"Goal added to mission: {goal_name}",
            )

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

        # Get mission ID
        mission_id = await ConversationMissionManager.get_conversation_mission(context)
        if not mission_id:
            await context.send_messages(
                NewConversationMessage(
                    content="You are not associated with a mission. Please create one first with `/create-mission`.",
                    message_type=MessageType.notice,
                )
            )
            return

        # Get user info
        participants = await context.get_participants()
        current_user_id = None
        for participant in participants.participants:
            if participant.role == "user":
                current_user_id = participant.id
                break

        if not current_user_id:
            current_user_id = "kb-creator"

        # Get existing KB or create new one
        kb = MissionStorage.read_mission_kb(mission_id)

        # If no KB exists, create a new one
        if not kb:
            kb = MissionKB(
                created_by=current_user_id,
                updated_by=current_user_id,
                conversation_id=str(context.id),
                sections={},
            )

        # Create the new section
        section = KBSection(
            title=title,
            content=section_content,
            order=len(kb.sections) + 1,
            updated_by=current_user_id,
        )

        # Add section to KB
        kb.sections[section.id] = section

        # Update KB metadata
        kb.updated_at = datetime.utcnow()
        kb.updated_by = current_user_id
        kb.version += 1

        # Save KB
        MissionStorage.write_mission_kb(mission_id, kb)
        success = True

        if success and kb:
            # Log the update
            await MissionStorage.log_mission_event(
                context=context,
                mission_id=mission_id,
                entry_type=LogEntryType.KB_UPDATE.value,
                message=f"Added KB section: {title}",
                related_entity_id=section.id,
            )

            # Notify linked conversations
            await MissionNotifier.notify_mission_update(
                context=context,
                mission_id=mission_id,
                update_type="kb_update",
                message=f"Knowledge base updated: added section '{title}'",
            )

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
        success, request = await MissionManager.create_field_request(
            context=context, title=title, description=description, priority=priority
        )

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
        success, status_obj = await MissionManager.update_mission_status(
            context=context, state=status, progress=progress, status_message=status_message
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
            requests = await MissionManager.get_field_requests(context)

            # Filter for active requests
            active_requests = [r for r in requests if r.status != RequestStatus.RESOLVED]

            if active_requests:
                request_list = ["## Active Field Requests\n"]

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
                        content="No active field requests found.",
                        message_type=MessageType.notice,
                    )
                )
            return

        # Resolve the field request
        success, field_request = await MissionManager.resolve_field_request(
            context=context, request_id=request_id, resolution=resolution
        )

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


async def handle_invite_command(context: ConversationContext, message: ConversationMessage, args: List[str]) -> None:
    """
    Legacy invite command handler - simplified to just show mission ID.
    
    With the simplified invitation system, we don't need to generate invitations.
    This function now just displays the mission ID as the invitation code.
    """
    try:
        # Get mission ID
        mission_id = await ConversationMissionManager.get_conversation_mission(context)
        if not mission_id:
            await context.send_messages(
                NewConversationMessage(
                    content="You are not associated with a mission. Please create one first with `/create-briefing`.",
                    message_type=MessageType.notice,
                )
            )
            return
            
        # Instead of creating a complex invitation, just display the mission ID
        await context.send_messages(
            NewConversationMessage(
                content=f"""## Mission Invitation
                
**Mission ID:** `{mission_id}`

Share this Mission ID with field personnel. They can join using:
`/join {mission_id}`

This Mission ID never expires and can be used by multiple field agents.
""",
                message_type=MessageType.chat,
            )
        )

        # Update all mission UI inspectors
        await MissionStorage.refresh_all_mission_uis(context, mission_id)

    except Exception as e:
        logger.exception(f"Error displaying mission ID: {e}")
        await context.send_messages(
            NewConversationMessage(
                content=f"Error displaying mission ID: {str(e)}",
                message_type=MessageType.notice,
            )
        )


async def handle_join_legacy_command(
    context: ConversationContext, message: ConversationMessage, args: List[str]
) -> None:
    """Handle the join command for legacy operation (non-setup mode)."""
    # Parse the command
    if not args:
        await context.send_messages(
            NewConversationMessage(
                content="Please specify an invitation code. Format: `/join invitation_code`",
                message_type=MessageType.notice,
            )
        )
        return

    invitation_code = args[0]

    try:
        # Use the proper MissionInvitation implementation from mission.py
        from .mission import MissionInvitation

        # Validate and redeem the invitation
        success, result_message = await MissionInvitation.redeem_invitation(context, invitation_code)

        # The redeem_invitation method handles all the operations, so we just need to send the result message
        await context.send_messages(
            NewConversationMessage(
                content=result_message,
                message_type=MessageType.chat if success else MessageType.notice,
            )
        )

        # Update all mission UI inspectors to reflect the change
        if success:
            mission_id = await ConversationMissionManager.get_conversation_mission(context)
            if mission_id:
                await MissionStorage.refresh_all_mission_uis(context, mission_id)

    except Exception as e:
        logger.exception(f"Error joining mission: {e}")
        await context.send_messages(
            NewConversationMessage(
                content=f"Error joining mission: {str(e)}",
                message_type=MessageType.notice,
            )
        )


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
        
        # Always show mission ID at the top for easy access
        mission_id = await MissionManager.get_mission_id(context)
        if mission_id:
            # Check if HQ or Field
            role = await MissionManager.get_mission_role(context)
            if role == MissionRole.HQ:
                # For HQ, make it prominent with instructions
                output.append(f"## Mission ID: `{mission_id}`")
                output.append(f"_Share this ID with field agents so they can join using_ `/join {mission_id}`\n")
            else:
                # For Field, just show the ID
                output.append(f"## Mission ID: `{mission_id}`\n")

        # Get mission briefing if requested
        if info_type in ["all", "briefing"]:
            briefing = await MissionManager.get_mission_briefing(context)

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
                    output.append("\n*No goals defined yet. Add goals with `/add-goal`.*")

        # Get mission KB if requested
        if info_type in ["all", "kb"]:
            kb = await MissionManager.get_mission_kb(context)

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
                output.append("*No knowledge base sections defined yet. Add sections with `/add-kb-section`.*")

        # Get mission status if requested
        if info_type in ["all", "status"]:
            status = await MissionManager.get_mission_status(context)

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
                output.append("*No mission status defined yet. Update status with `/update-status`.*")

        # Get field requests if requested
        if info_type in ["all", "requests"]:
            requests = await MissionManager.get_field_requests(context)

            if requests:
                output.append("\n## Field Requests\n")

                # Group requests by status
                active_requests = [
                    r for r in requests if r.status != RequestStatus.RESOLVED and r.status != RequestStatus.CANCELLED
                ]
                resolved_requests = [
                    r for r in requests if r.status == RequestStatus.RESOLVED or r.status == RequestStatus.CANCELLED
                ]

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
        # Get mission ID
        mission_id = await ConversationMissionManager.get_conversation_mission(context)
        if not mission_id:
            await context.send_messages(
                NewConversationMessage(
                    content="You are not associated with a mission.",
                    message_type=MessageType.notice,
                )
            )
            return

        # Get all linked conversations
        linked_conversation_ids = await ConversationMissionManager.get_linked_conversations(context)

        if not linked_conversation_ids:
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

        # In the simplified implementation, we don't have detail about the linked conversations
        # For a more complete implementation, we would need to get information
        # about each linked conversation

        # For now, just report that we have no other field personnel
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
        # Get mission ID
        mission_id = await ConversationMissionManager.get_conversation_mission(context)
        if not mission_id:
            await context.send_messages(
                NewConversationMessage(
                    content="You are not associated with a mission.",
                    message_type=MessageType.notice,
                )
            )
            return

        # Get all linked conversations
        linked_conversation_ids = await ConversationMissionManager.get_linked_conversations(context)

        if not linked_conversation_ids:
            await context.send_messages(
                NewConversationMessage(
                    content="No linked conversations found.",
                    message_type=MessageType.notice,
                )
            )
            return

        # In the simplified implementation, we just inform the user that the feature is not implemented
        await context.send_messages(
            NewConversationMessage(
                content=f"Revoking access for '{username}' is not yet implemented in this version.",
                message_type=MessageType.notice,
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

# Setup mode commands
command_registry.register_command(
    "start-hq",
    handle_start_hq_command,
    "Create a new mission with this conversation as HQ",
    "/start-hq [Mission Name|Mission description]",
    "/start-hq Operation Firewall|Investigate and mitigate the recent network breach",
    None,  # Available to all roles during setup
)

command_registry.register_command(
    "join",
    handle_join_command,
    "Join an existing mission with an invitation code",
    "/join invitation_code",
    "/join abc123:xyz456",
    None,  # Available to all roles
)

# General commands (available to all)
command_registry.register_command(
    "help",
    handle_help_command,
    "Get help with available commands",
    "/help [command]",
    "/help mission-info",
    None,  # Available to all roles
)

command_registry.register_command(
    "mission-info",
    handle_mission_info_command,
    "View mission information",
    "/mission-info [briefing|kb|status|requests]",
    "/mission-info briefing",
    None,  # Available to all roles
)

# Team management commands
# "invite" command removed - mission ID is now used directly for invitations

command_registry.register_command(
    "join",
    handle_join_command,
    "Join a mission using its mission ID",
    "/join mission_id",
    "/join abc123-def-456",
    None,  # Available to all roles (anyone can join if they have the mission ID)
)

command_registry.register_command(
    "list-participants",
    handle_list_participants_command,
    "List all mission participants",
    "/list-participants",
    "/list-participants",
    ["hq"],  # Only HQ can list participants
)

command_registry.register_command(
    "revoke",
    handle_revoke_access_command,
    "Revoke a participant's access to the mission",
    "/revoke username",
    "/revoke john.doe",
    ["hq"],  # Only HQ can revoke access
)

# HQ commands
command_registry.register_command(
    "create-briefing",
    handle_create_briefing_command,
    "Create a mission briefing",
    "/create-briefing Mission Name|Mission description",
    "/create-briefing Investigate Network Outage|The network in Building C went down at 3pm. We need to identify the cause and restore service.",
    ["hq"],  # Only HQ can create briefings
)

command_registry.register_command(
    "add-goal",
    handle_add_goal_command,
    "Add a goal to the mission briefing",
    "/add-goal Goal Name|Goal description|Success criterion 1;Success criterion 2",
    "/add-goal Restore Network Service|Get Building C back online|Service restored to all floors;Verified connectivity for all devices",
    ["hq"],  # Only HQ can add goals
)

command_registry.register_command(
    "add-kb-section",
    handle_add_kb_section_command,
    "Add a section to the mission knowledge base",
    "/add-kb-section Section Title|Section content",
    "/add-kb-section Network Diagram|Building C uses the following topology: [diagram details]",
    ["hq"],  # Only HQ can add KB sections
)

command_registry.register_command(
    "resolve-request",
    handle_resolve_request_command,
    "Resolve a field request",
    "/resolve-request request_id|Resolution information",
    "/resolve-request abc123|The login credentials are admin/NetworkPass2024",
    ["hq"],  # Only HQ can resolve requests
)

# Field commands
command_registry.register_command(
    "request-info",
    handle_request_info_command,
    "Request information or assistance from HQ",
    "/request-info Request Title|Request description|priority",
    "/request-info Need Server Room Access|I need the door code for the server room in Building C|high",
    ["field"],  # Only field can create requests
)

command_registry.register_command(
    "update-status",
    handle_update_status_command,
    "Update mission status and progress",
    "/update-status status|progress|message",
    "/update-status in_progress|50|Identified faulty switch on floor 3, working on replacement",
    ["field"],  # Only field can update status
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
    from .mission_storage import ConversationMissionManager

    # First check conversation metadata
    conversation = await context.get_conversation()
    metadata = conversation.metadata or {}

    # Check if setup is complete
    setup_complete = metadata.get("setup_complete", False)
    
    # If not set in local metadata, try to get it from the state API via the state events
    if not setup_complete:
        try:
            # Get state directly from conversation state
            from .state_inspector import MissionInspectorStateProvider
            inspector = MissionInspectorStateProvider(None)
            state_data = await inspector.get(context)
            
            if state_data and state_data.data and state_data.data.get("content"):
                content = state_data.data.get("content", "")
                # Check if content indicates we're in HQ or Field mode (not in setup mode)
                if "Role: HQ" in content or "Role: Field" in content:
                    setup_complete = True
                    # Extract role from content
                    if "Role: HQ" in content:
                        metadata["mission_role"] = "hq"
                        metadata["assistant_mode"] = "hq"
                    else:
                        metadata["mission_role"] = "field"
                        metadata["assistant_mode"] = "field"
                    metadata["setup_complete"] = True
                    
                    logger.info(f"Found role in state inspector: {metadata['mission_role']}")
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
        # Always allow these commands in setup mode
        setup_commands = ["start-hq", "join", "help"]

        if command_name in setup_commands:
            # If the command is a setup command, process it
            if command_name == "help":
                await handle_help_command(context, message, args)
                return True
            elif command_name in command_registry.commands:
                await command_registry.commands[command_name]["handler"](context, message, args)
                return True
        else:
            # Show setup required message for non-setup commands
            await context.send_messages(
                NewConversationMessage(
                    content=(
                        "**Setup Required**\n\n"
                        "You need to set up the assistant before using other commands. Please use one of these commands:\n\n"
                        "- `/start-hq` - Create a new mission as HQ\n"
                        "- `/join <code>` - Join an existing mission as a Field agent\n"
                        "- `/help` - Get help with available commands"
                    ),
                    message_type=MessageType.notice,
                )
            )
            return True

    # Standard command processing for non-setup mode
    metadata_role = metadata.get("mission_role")

    # Then check the stored role from mission storage - this is the authoritative source
    stored_role = await ConversationMissionManager.get_conversation_role(context)
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
        # Otherwise use metadata or default to HQ
        role = metadata_role or "hq"  # Default to HQ if not set

    # Process the command through the registry
    return await command_registry.process_command(context, message, role)
