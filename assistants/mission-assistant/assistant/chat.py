# Copyright (c) Microsoft. All rights reserved.

# An example for building a simple chat assistant using the AssistantApp from
# the semantic-workbench-assistant package.
#
# This example demonstrates how to use the AssistantApp to create a chat assistant,
# to add additional configuration fields and UI schema for the configuration fields,
# and to handle conversation events to respond to messages in the conversation.

# region Required
#
# The code in this region demonstrates the minimal code required to create a chat assistant
# using the AssistantApp class from the semantic-workbench-assistant package. This code
# demonstrates how to create an AssistantApp instance, define the service ID, name, and
# description, and create the FastAPI app instance. Start here to build your own chat
# assistant using the AssistantApp class.
#
# The code that follows this region is optional and demonstrates how to add event handlers
# to respond to conversation events. You can use this code as a starting point for building
# your own chat assistant with additional functionality.
#


import logging
import re
from datetime import datetime
from typing import Any

import deepmerge
import openai_client
import tiktoken
from content_safety.evaluators import CombinedContentSafetyEvaluator
from openai.types.chat import ChatCompletionMessageParam
from semantic_workbench_api_model import workbench_model
from semantic_workbench_api_model.workbench_model import (
    AssistantStateEvent,
    ConversationEvent,
    ConversationMessage,
    MessageType,
    NewConversationMessage,
    UpdateParticipant,
)
from semantic_workbench_assistant.assistant_app import (
    AssistantApp,
    BaseModelAssistantConfig,
    ContentSafety,
    ContentSafetyEvaluator,
    ConversationContext,
)

from .artifact_messaging import ArtifactManager, ArtifactMessenger
from .artifacts import ArtifactType
from .config import AssistantConfigModel
from .mission import ConversationClientManager, FileSynchronizer, MissionManager, MissionStateManager

logger = logging.getLogger(__name__)

#
# define the service ID, name, and description
#

# the service id to be registered in the workbench to identify the assistant
service_id = "mission-assistant.workbench-explorer"
# the name of the assistant service, as it will appear in the workbench UI
service_name = "Mission Assistant"
# a description of the assistant service, as it will appear in the workbench UI
service_description = "A mediator assistant that facilitates file sharing between conversations."

#
# create the configuration provider, using the extended configuration model
#
assistant_config = BaseModelAssistantConfig(AssistantConfigModel)


# define the content safety evaluator factory
async def content_evaluator_factory(context: ConversationContext) -> ContentSafetyEvaluator:
    config = await assistant_config.get(context.assistant)
    return CombinedContentSafetyEvaluator(config.content_safety_config)


content_safety = ContentSafety(content_evaluator_factory)


# create the AssistantApp instance
assistant = AssistantApp(
    assistant_service_id=service_id,
    assistant_service_name=service_name,
    assistant_service_description=service_description,
    config_provider=assistant_config.provider,
    content_interceptor=content_safety,
)

#
# create the FastAPI app instance
#
app = assistant.fastapi_app()


# endregion


# region Optional
#
# Note: The code in this region is specific to this example and is not required for a basic assistant.
#
# The AssistantApp class provides a set of decorators for adding event handlers to respond to conversation
# events. In VS Code, typing "@assistant." (or the name of your AssistantApp instance) will show available
# events and methods.
#
# See the semantic-workbench-assistant AssistantApp class for more information on available events and methods.
# Examples:
# - @assistant.events.conversation.on_created (event triggered when the assistant is added to a conversation)
# - @assistant.events.conversation.participant.on_created (event triggered when a participant is added)
# - @assistant.events.conversation.message.on_created (event triggered when a new message of any type is created)
# - @assistant.events.conversation.message.chat.on_created (event triggered when a new chat message is created)
#


@assistant.events.conversation.message.chat.on_created
async def on_message_created(
    context: ConversationContext, event: ConversationEvent, message: ConversationMessage
) -> None:
    """
    Handle the event triggered when a new chat message is created in the conversation.

    **Note**
    - This event handler is specific to chat messages.
    - To handle other message types, you can add additional event handlers for those message types.
      - @assistant.events.conversation.message.log.on_created
      - @assistant.events.conversation.message.command.on_created
      - ...additional message types
    - To handle all message types, you can use the root event handler for all message types:
      - @assistant.events.conversation.message.on_created
    """

    # update the participant status to indicate the assistant is thinking
    await context.update_participant_me(UpdateParticipant(status="thinking..."))
    try:
        # Get the conversation's role (HQ or Field)
        # Get conversation to access metadata
        conversation = await context.get_conversation()
        metadata = conversation.metadata or {}
        role = metadata.get("mission_role")

        # If role isn't set yet, detect it now
        if not role:
            role = await detect_assistant_role(context)
            metadata["mission_role"] = role
            # Update conversation metadata through appropriate method
            await context.send_conversation_state_event(
                AssistantStateEvent(
                    state_id="mission_role",
                    event="updated",
                    state=None
                )
            )

        # Prepare custom system message based on role
        role_specific_prompt = ""

        if role == "hq":
            # HQ-specific instructions
            role_specific_prompt = """
You are operating in HQ Mode (Definition Stage). Your responsibilities include:
- Helping create and refine the Mission Briefing with goals and success criteria
- Building a comprehensive Mission Knowledge Base with mission-critical information
- Providing guidance on mission preparation and coordination
- Responding to Field Requests from mission participants
- Controlling the "Ready for Field" gate
- Maintaining an overview of mission progress

Use a strategic, guidance-oriented tone focused on mission definition and support.
"""
        else:
            # Field-specific instructions
            role_specific_prompt = """
You are operating in Field Mode (Working Stage). Your responsibilities include:
- Helping field personnel understand and execute the mission
- Providing access to the Mission Knowledge Base created by HQ
- Logging information gaps and blockers as Field Requests
- Reporting progress on mission goals and success criteria
- Updating Mission Status with completed tasks
- Tracking progress toward the "Mission Completion" gate

Use a practical, operational tone focused on mission execution and problem-solving.
"""

        # Add role-specific metadata to pass to the LLM
        role_metadata = {
            "mission_role": role,
            "role_description": "HQ Mode (Definition Stage)" if role == "hq" else "Field Mode (Working Stage)",
            "debug": {"content_safety": event.data.get(content_safety.metadata_key, {})},
        }

        # respond to the message with role-specific context
        await respond_to_conversation(
            context, message=message, metadata=role_metadata, role_specific_prompt=role_specific_prompt
        )
    finally:
        # update the participant status to indicate the assistant is done thinking
        await context.update_participant_me(UpdateParticipant(status=None))


@assistant.events.conversation.message.command.on_created
async def on_command_created(
    context: ConversationContext, event: ConversationEvent, message: ConversationMessage
) -> None:
    """
    Handle command messages, especially looking for mission-related commands.
    """
    # update the participant status to indicate the assistant is thinking
    await context.update_participant_me(UpdateParticipant(status="processing command..."))
    try:
        # Get the configuration
        config = await assistant_config.get(context.assistant)
        invite_command = config.mission_config.invite_command
        join_command = config.mission_config.join_command

        # Get the conversation's role (HQ or Field)
        conversation = await context.get_conversation()
        metadata = conversation.metadata or {}
        role = metadata.get("mission_role")

        # If role isn't set yet, detect it now
        if not role:
            role = await detect_assistant_role(context)
            metadata["mission_role"] = role
            await context.send_conversation_state_event(
                AssistantStateEvent(
                    state_id="mission_role",
                    event="updated",
                    state=None
                )
            )

        # Process invitation commands (available to all)
        if message.content.strip().startswith(f"/{invite_command}"):
            await MissionManager.process_invite_command(context, message, invite_command)
            return

        if message.content.strip().startswith(f"/{join_command}"):
            await MissionManager.process_join_command(context, message, join_command)
            return

        # Process role-specific commands
        if role == "hq":
            # HQ-specific commands

            # Process mission briefing creation command
            if message.content.strip().startswith("/create-briefing"):
                await process_create_briefing_command(context, message)
                return

            # Process goal addition command
            if message.content.strip().startswith("/add-goal"):
                await process_add_goal_command(context, message)
                return

            # Process KB section addition command
            if message.content.strip().startswith("/add-kb-section"):
                await process_add_kb_section_command(context, message)
                return

            # Process field request resolution
            if message.content.strip().startswith("/resolve-request"):
                await process_resolve_request_command(context, message)
                return

            # HQ-specific commands for managing participants
            if message.content.strip().startswith(f"/{config.mission_config.sender_config.list_participants_command}"):
                await process_list_participants_command(context, message)
                return

            if message.content.strip().startswith(f"/{config.mission_config.sender_config.revoke_access_command}"):
                await process_revoke_access_command(context, message)
                return

        elif role == "field":
            # Field-specific commands

            # Process field request command
            if message.content.strip().startswith("/request-info"):
                await process_field_request_command(context, message)
                return

            # Field operations can update mission status
            if message.content.strip().startswith("/update-status"):
                await process_status_update_command(context, message)
                return

            # Field-specific commands
            if message.content.strip().startswith(f"/{config.mission_config.receiver_config.status_command}"):
                # Redirect to mission-info for backward compatibility
                await process_mission_info_command(context, message)
                return

        # Commands available to both roles
        if message.content.strip().startswith("/mission-info"):
            await process_mission_info_command(context, message)
            return

        # Help command
        if message.content.strip().startswith("/help"):
            await process_help_command(context, message, role)
            return

        # If command is not recognized or not allowed for this role
        content = message.content.strip()
        command = content.split(" ")[0] if " " in content else content

        if role == "hq" and command in ["/request-info"]:
            await context.send_messages(
                NewConversationMessage(
                    content=f"The {command} command is only available in Field Mode. You are currently in HQ Mode.",
                    message_type=MessageType.notice,
                )
            )
            return

        if role == "field" and command in ["/create-briefing", "/add-goal", "/add-kb-section", "/resolve-request"]:
            await context.send_messages(
                NewConversationMessage(
                    content=f"The {command} command is only available in HQ Mode. You are currently in Field Mode.",
                    message_type=MessageType.notice,
                )
            )
            return

        # For other commands, respond normally
        await respond_to_conversation(
            context,
            message=message,
            metadata={"debug": {"content_safety": event.data.get(content_safety.metadata_key, {})}},
        )
    finally:
        # update the participant status to indicate the assistant is done thinking
        await context.update_participant_me(UpdateParticipant(status=None))


@assistant.events.conversation.file.on_created
async def on_file_created(context: ConversationContext, event: workbench_model.ConversationEvent, file: workbench_model.File) -> None:
    """
    Handle when a file is created in the conversation, sync to linked conversations if needed.
    """
    try:
        # Get config to check if auto-sync is enabled
        config = await assistant_config.get(context.assistant)
        if not config.mission_config.auto_sync_files:
            return

        # Get the file name from the File object
        filename = file.filename
        if not filename:
            return

        # Check if file should be synced to other conversations
        target_conversations = await MissionManager.should_sync_file(context, filename)
        if not target_conversations:
            return

        # Notify about file synchronization
        await context.send_messages(
            NewConversationMessage(
                content=f"File '{filename}' has been synchronized with {len(target_conversations)} linked conversation(s).",
                message_type=MessageType.notice,
            )
        )

        # In a real implementation, synchronize files to target conversations
        for target_id in target_conversations:
            await FileSynchronizer.sync_file(context, target_id, filename)

    except Exception as e:
        logger.exception(f"Error handling file creation: {e}")


@assistant.events.conversation.file.on_updated
async def on_file_updated(context: ConversationContext, event: workbench_model.ConversationEvent, file: workbench_model.File) -> None:
    """
    Handle when a file is updated in the conversation, sync updates to linked conversations.
    """
    try:
        # Identical logic to on_file_created, could be refactored to a common method
        # Get config to check if auto-sync is enabled
        config = await assistant_config.get(context.assistant)
        if not config.mission_config.auto_sync_files:
            return

        # Get the file name from the File object
        filename = file.filename
        if not filename:
            return

        # Check if file should be synced to other conversations
        target_conversations = await MissionManager.should_sync_file(context, filename)
        if not target_conversations:
            return

        # Notify about file synchronization
        await context.send_messages(
            NewConversationMessage(
                content=f"Updated file '{filename}' has been synchronized with {len(target_conversations)} linked conversation(s).",
                message_type=MessageType.notice,
            )
        )

        # In a real implementation, synchronize files to target conversations
        for target_id in target_conversations:
            await FileSynchronizer.sync_file(context, target_id, filename)

    except Exception as e:
        logger.exception(f"Error handling file update: {e}")


# Handle artifact messages (sent between conversations)
@assistant.events.conversation.message.notice.on_created
async def on_notice_created(
    context: ConversationContext, event: ConversationEvent, message: ConversationMessage
) -> None:
    """
    Handle notice messages, which may contain artifact data.
    """
    metadata = message.metadata or {}

    # Check if this is an artifact message
    if "artifact_message" in metadata:
        # Process the artifact message
        await ArtifactMessenger.process_artifact_message(context, message)
        return

    # Check if this is an artifact request
    if "artifact_request" in metadata:
        # Process the artifact request
        await ArtifactMessenger.process_artifact_request(context, message)
        return


# Role detection for the mission assistant
async def detect_assistant_role(context: ConversationContext) -> str:
    """
    Detects whether this conversation is in HQ Mode or Field Mode.

    Returns:
        "hq" if in HQ Mode, "field" if in Field Mode
    """
    try:
        # Check if this conversation has an active invitation from another conversation
        links = await MissionStateManager.get_links(context)

        # If we have linked to conversations but didn't create a briefing,
        # we're likely in Field Mode
        if links.linked_conversations:
            # Check if this conversation created a mission briefing
            from .artifacts import MissionBriefing
            briefings = await ArtifactMessenger.get_artifacts_by_type(context, MissionBriefing)

            # If we have briefings that were created by this conversation, we're in HQ Mode
            for briefing in briefings:
                if briefing.conversation_id == str(context.id):
                    return "hq"

            # If we have links to other conversations and didn't create the briefing,
            # we're in Field Mode
            for conv_id, linked_conv in links.linked_conversations.items():
                if conv_id != str(context.id):
                    return "field"

        # Default to HQ Mode for new conversations
        return "hq"

    except Exception as e:
        logger.exception(f"Error detecting assistant role: {e}")
        # Default to HQ Mode if detection fails
        return "hq"


# Handle the event triggered when the assistant is added to a conversation.
@assistant.events.conversation.on_created
async def on_conversation_created(context: ConversationContext) -> None:
    """
    Handle the event triggered when the assistant is added to a conversation.
    """
    # get the assistant's configuration
    config = await assistant_config.get(context.assistant)

    # Detect whether this is an HQ or Field conversation
    role = await detect_assistant_role(context)

    # Store the role in conversation metadata for future reference
    conversation = await context.get_conversation()
    metadata = conversation.metadata or {}
    metadata["mission_role"] = role
    await context.send_conversation_state_event(
        AssistantStateEvent(
            state_id="mission_role",
            event="updated",
            state=None
        )
    )

    # Select the appropriate welcome message based on role
    if role == "hq":
        welcome_message = config.mission_config.sender_config.welcome_message
    else:
        welcome_message = config.mission_config.receiver_config.welcome_message

    # send the welcome message to the conversation
    await context.send_messages(
        NewConversationMessage(
            content=welcome_message,
            message_type=MessageType.chat,
            metadata={"generated_content": False},
        )
    )

    # If this is an HQ conversation and proactive guidance is enabled,
    # provide guidance on getting started
    if role == "hq" and config.mission_config.proactive_guidance:
        await context.send_messages(
            NewConversationMessage(
                content=config.mission_config.sender_config.prompt_for_files,
                message_type=MessageType.chat,
            )
        )


# Process mission-related commands


async def process_create_briefing_command(context: ConversationContext, message: ConversationMessage) -> None:
    """
    Process a command to create a mission briefing.
    Format: /create-briefing <mission_name>|<mission_description>
    """
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


async def process_add_goal_command(context: ConversationContext, message: ConversationMessage) -> None:
    """
    Process a command to add a goal to the mission briefing.
    Format: /add-goal <goal_name>|<goal_description>|<criteria1>;<criteria2>;<etc>
    """
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
        from .artifacts import MissionBriefing
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

        # Create the goal with success criteria
        from .artifacts import MissionGoal, SuccessCriterion

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

        briefing.updated_at = datetime.utcnow()
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


async def process_add_kb_section_command(context: ConversationContext, message: ConversationMessage) -> None:
    """
    Process a command to add a section to the mission knowledge base.
    Format: /add-kb-section <title>|<content>
    """
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
        from .artifacts import MissionKB
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


async def process_field_request_command(context: ConversationContext, message: ConversationMessage) -> None:
    """
    Process a command to create a field request.
    Format: /request-info <title>|<description>|<priority>
    """
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
        from .artifacts import RequestPriority

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


async def process_status_update_command(context: ConversationContext, message: ConversationMessage) -> None:
    """
    Process a command to update mission status.
    Format: /update-status <status>|<progress>|<message>
    """
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


async def process_list_participants_command(context: ConversationContext, message: ConversationMessage) -> None:
    """
    Process a command to list all participants in the mission.
    Format: /list-participants
    """
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


async def process_help_command(context: ConversationContext, message: ConversationMessage, role: str) -> None:
    """
    Process a help command to show available commands.
    Format: /help
    """
    try:
        # Get configuration
        config = await assistant_config.get(context.assistant)

        # Generate help text based on role
        if role == "hq":
            help_text = f"""
## Mission Assistant Commands (HQ Mode)

### Mission Configuration
- `/create-briefing Mission Name|Mission description` - Create a mission briefing
- `/add-goal Goal Name|Goal description|Success criterion 1;Success criterion 2` - Add a goal to the mission briefing
- `/add-kb-section Section Title|Section content` - Add a section to the mission knowledge base

### Team Management
- `/{config.mission_config.invite_command} username` - Invite a team member to join the mission
- `/{config.mission_config.sender_config.list_participants_command}` - List all mission participants
- `/{config.mission_config.sender_config.revoke_access_command} username` - Revoke a team member's access to the mission

### Field Request Management
- `/resolve-request request_id|resolution` - Resolve a field request with the provided information

### Information
- `/mission-info [briefing|kb|status|requests]` - View mission information
- `/help` - Show this help message

As HQ, you are responsible for defining the mission, creating mission knowledge, and coordinating field personnel.
"""
        else:
            help_text = f"""
## Mission Assistant Commands (Field Mode)

### Field Operations
- `/request-info Request Title|Description of what you need|priority` - Request information or report a blocker
- `/update-status status|progress|message` - Update mission status and progress
- `/{config.mission_config.receiver_config.status_command}` - View mission status

### Information
- `/mission-info [briefing|kb|status|requests]` - View mission information
- `/help` - Show this help message

### Team Management
- `/{config.mission_config.join_command} invitation_code` - Join a mission you've been invited to

As Field personnel, you can access mission knowledge, request information, and report progress on mission goals.
"""

        # Send the help message
        await context.send_messages(
            NewConversationMessage(
                content=help_text,
                message_type=MessageType.chat,
            )
        )

    except Exception as e:
        logger.exception(f"Error processing help command: {e}")
        await context.send_messages(
            NewConversationMessage(
                content=f"Error displaying help: {str(e)}",
                message_type=MessageType.notice,
            )
        )


async def process_revoke_access_command(context: ConversationContext, message: ConversationMessage) -> None:
    """
    Process a command to revoke access for a mission participant.
    Format: /revoke username
    """
    # Parse the command
    content = message.content.strip()
    parts = content.split(" ", 1)

    if len(parts) < 2 or not parts[1].strip():
        await context.send_messages(
            NewConversationMessage(
                content="Please specify a username to revoke access. Format: `/revoke username`",
                message_type=MessageType.notice,
            )
        )
        return

    username = parts[1].strip()

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


async def process_resolve_request_command(context: ConversationContext, message: ConversationMessage) -> None:
    """
    Process a command to resolve a field request.
    Format: /resolve-request <request_id>|<resolution>
    """
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
            await process_mission_info_command(
                context,
                ConversationMessage(
                    id=message.id,
                    sender=message.sender,
                    content="/mission-info requests",
                    timestamp=message.timestamp,
                    message_type=MessageType.command,
                    content_type="text/plain",
                    filenames=[],
                    metadata={},
                    has_debug_data=False
                ),
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
                    content="Use `/mission-info requests` to view all field requests and their IDs.",
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


async def process_mission_info_command(context: ConversationContext, message: ConversationMessage) -> None:
    """
    Process a command to view mission information.
    Format: /mission-info [briefing|kb|status|requests]
    """
    # Parse the command
    content = message.content.strip()[len("/mission-info") :].strip().lower()

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
            from .artifacts import MissionBriefing
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
            from .artifacts import MissionKB
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
            from .artifacts import MissionStatus
            status_artifacts = await ArtifactMessenger.get_artifacts_by_type(context, MissionStatus)

            if status_artifacts:
                status = status_artifacts[0]  # Most recent status

                output.append("\n## Mission Status\n")
                output.append(f"**Current Status**: {status.status}")

                if status.progress is not None:
                    output.append(f"**Overall Progress**: {status.progress}%")

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
            from .artifacts import FieldRequest
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


# endregion


# region Custom
#
# This code was added specifically for this example to demonstrate how to respond to conversation
# messages using the OpenAI API. For your own assistant, you could replace this code with your own
# logic for responding to conversation messages and add any additional functionality as needed.
#


# demonstrates how to respond to a conversation message using the OpenAI API.
async def respond_to_conversation(
    context: ConversationContext,
    message: ConversationMessage,
    metadata: dict[str, Any] = {},
    role_specific_prompt: str = "",
) -> None:
    """
    Respond to a conversation message.
    """

    # define the metadata key for any metadata created within this method
    method_metadata_key = "respond_to_conversation"

    # get the assistant's configuration, supports overwriting defaults from environment variables
    config = await assistant_config.get(context.assistant)

    # get the list of conversation participants
    participants_response = await context.get_participants(include_inactive=True)

    # establish a token to be used by the AI model to indicate no response
    silence_token = "{{SILENCE}}"

    # create a system message, start by adding the guardrails prompt
    system_message_content = config.guardrails_prompt

    # add the instruction prompt and the assistant name
    system_message_content += f'\n\n{config.instruction_prompt}\n\nYour name is "{context.assistant.name}".'

    # Add role-specific instructions if provided
    if role_specific_prompt:
        system_message_content += f"\n\n{role_specific_prompt}"

    # if this is a multi-participant conversation, add a note about the participants
    if len(participants_response.participants) > 2:
        system_message_content += (
            "\n\n"
            f"There are {len(participants_response.participants)} participants in the conversation,"
            " including you as the assistant and the following users:"
            + ",".join([
                f' "{participant.name}"'
                for participant in participants_response.participants
                if participant.id != context.assistant.id
            ])
            + "\n\nYou do not need to respond to every message. Do not respond if the last thing said was a closing"
            " statement such as 'bye' or 'goodbye', or just a general acknowledgement like 'ok' or 'thanks'. Do not"
            f' respond as another user in the conversation, only as "{context.assistant.name}".'
            " Sometimes the other users need to talk amongst themselves and that is ok. If the conversation seems to"
            f' be directed at you or the general audience, go ahead and respond.\n\nSay "{silence_token}" to skip'
            " your turn."
        )

    # create the completion messages for the AI model and add the system message
    completion_messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": system_message_content,
        }
    ]

    # get the current token count and track the tokens used as messages are added
    current_tokens = 0
    # add the token count for the system message
    current_tokens += get_token_count(system_message_content)

    # consistent formatter that includes the participant name for multi-participant and name references
    def format_message(message: ConversationMessage) -> str:
        # get the participant name for the message sender
        conversation_participant = next(
            (
                participant
                for participant in participants_response.participants
                if participant.id == message.sender.participant_id
            ),
            None,
        )
        participant_name = conversation_participant.name if conversation_participant else "unknown"

        # format the message content with the participant name and message timestamp
        message_datetime = message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return f"[{participant_name} - {message_datetime}]: {message.content}"

    # get messages before the current message
    messages_response = await context.get_messages(before=message.id)
    messages = messages_response.messages + [message]

    # create a list of the recent chat history messages to send to the AI model
    history_messages: list[ChatCompletionMessageParam] = []
    # iterate over the messages in reverse order to get the most recent messages first
    for message in reversed(messages):
        # add the token count for the message and check if the token limit has been reached
        message_tokens = get_token_count(format_message(message))
        current_tokens += message_tokens
        if current_tokens > config.request_config.max_tokens - config.request_config.response_tokens:
            # if the token limit has been reached, stop adding messages
            break

        # add the message to the history messages
        if message.sender.participant_id == context.assistant.id:
            # this is an assistant message
            history_messages.append({
                "role": "assistant",
                "content": format_message(message),
            })
        else:
            # this is a user message
            history_messages.append({
                "role": "user",
                "content": format_message(message),
            })

    # reverse the history messages to send the most recent messages first
    history_messages.reverse()

    # add the history messages to the completion messages
    completion_messages.extend(history_messages)

    # evaluate the content for safety
    # disabled because the OpenAI and Azure OpenAI services already have content safety checks
    # and we are more interested in running the generated responses through the content safety checks
    # which are being handled by the content safety interceptor on the assistant
    # this code is therefore included here for reference on how to call the content safety evaluator
    # from within the assistant code

    # content_evaluator = await content_evaluator_factory(context)
    # evaluation = await content_evaluator.evaluate([message.content for message in messages])

    # deepmerge.always_merger.merge(
    #     metadata,
    #     {
    #         "debug": {
    #             f"{assistant.content_interceptor.metadata_key}": {
    #                 f"{method_metadata_key}": {
    #                     "evaluation": evaluation.model_dump(),
    #                 },
    #             },
    #         },
    #     },
    # )

    # if evaluation.result == ContentSafetyEvaluationResult.Fail:
    #     # send a notice to the user that the content safety evaluation failed
    #     deepmerge.always_merger.merge(
    #         metadata,
    #         {"generated_content": False},
    #     )
    #     await context.send_messages(
    #         NewConversationMessage(
    #             content=evaluation.note or "Content safety evaluation failed.",
    #             message_type=MessageType.notice,
    #             metadata=metadata,
    #         )
    #     )
    #     return

    # Get the conversation's role
    from .mission_tools import get_mission_tools

    conversation = await context.get_conversation()
    metadata = conversation.metadata or {}
    role = metadata.get("mission_role", "hq")  # Default to HQ if not set

    # Set up mission tools for the completion based on role
    mission_tools = await get_mission_tools(context, role)

    # Generate a response from the AI model with tools
    async with openai_client.create_client(config.service_config, api_version="2024-06-01") as client:
        try:
            # Create a completion dictionary for tool call handling
            completion_args = {
                "messages": completion_messages,
                "model": config.request_config.openai_model,
                "max_tokens": config.request_config.response_tokens,
            }

            # If the messaging API version supports tool functions, use them
            try:
                from openai_client.tools import complete_with_tool_calls

                # Call the completion API with tool functions
                logger.info("Using tool functions for completions")

                tool_completion, tool_messages = await complete_with_tool_calls(
                    async_client=client,
                    completion_args=completion_args,
                    tool_functions=mission_tools.tool_functions,
                    metadata=metadata,
                )

                # Get the final assistant message content
                content = None
                for msg in tool_messages:
                    if msg["role"] == "assistant" and "content" in msg and msg["content"]:
                        content = msg["content"]

                if not content:
                    # Fallback if no final message was generated
                    content = "I've processed your request, but couldn't generate a proper response."

                # Add tool call message exchange to metadata for debugging
                deepmerge.always_merger.merge(
                    metadata,
                    {
                        "debug": {
                            f"{method_metadata_key}": {
                                "tool_messages": str(tool_messages),
                                "response": tool_completion.model_dump()
                                if tool_completion
                                else "[no response from openai]",
                            },
                        }
                    },
                )

            except (ImportError, AttributeError):
                # Fallback to standard completions if tool calls aren't supported
                logger.info("Tool functions not supported, falling back to standard completion")

                # Call the OpenAI chat completion endpoint to get a response
                completion = await client.chat.completions.create(**completion_args)

                # Get the content from the completion response
                content = completion.choices[0].message.content

                # Merge the completion response into the passed in metadata
                deepmerge.always_merger.merge(
                    metadata,
                    {
                        "debug": {
                            f"{method_metadata_key}": {
                                "request": completion_args,
                                "response": completion.model_dump() if completion else "[no response from openai]",
                            },
                        }
                    },
                )

        except Exception as e:
            logger.exception(f"exception occurred calling openai chat completion: {e}")
            # if there is an error, set the content to an error message
            content = "An error occurred while calling the OpenAI API. Is it configured correctly?"

            # merge the error into the passed in metadata
            deepmerge.always_merger.merge(
                metadata,
                {
                    "debug": {
                        f"{method_metadata_key}": {
                            "request": {
                                "model": config.request_config.openai_model,
                                "messages": completion_messages,
                            },
                            "error": str(e),
                        },
                    }
                },
            )

    # set the message type based on the content
    message_type = MessageType.chat

    # various behaviors based on the content
    if content:
        # strip out the username from the response
        if isinstance(content, str) and content.startswith("["):
            content = re.sub(r"\[.*\]:\s", "", content)

        # check for the silence token, in case the model chooses not to respond
        # model sometimes puts extra spaces in the response, so remove them
        # when checking for the silence token
        if isinstance(content, str) and content.replace(" ", "") == silence_token:
            # normal behavior is to not respond if the model chooses to remain silent
            # but we can override this behavior for debugging purposes via the assistant config
            if config.enable_debug_output:
                # update the metadata to indicate the assistant chose to remain silent
                deepmerge.always_merger.merge(
                    metadata,
                    {
                        "debug": {
                            f"{method_metadata_key}": {
                                "silence_token": True,
                            },
                        },
                        "attribution": "debug output",
                        "generated_content": False,
                    },
                )
                # send a notice to the user that the assistant chose to remain silent
                await context.send_messages(
                    NewConversationMessage(
                        message_type=MessageType.notice,
                        content="[assistant chose to remain silent]",
                        metadata=metadata,
                    )
                )
            return

        # override message type if content starts with "/", indicating a command response
        if isinstance(content, str) and content.startswith("/"):
            message_type = MessageType.command_response

    # send the response to the conversation
    await context.send_messages(
        NewConversationMessage(
            content=str(content) if content is not None else "[no response from openai]",
            message_type=message_type,
            metadata=metadata,
        )
    )


# this method is used to get the token count of a string.
def get_token_count(string: str) -> int:
    """
    Get the token count of a string.
    """
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(string))


# endregion
