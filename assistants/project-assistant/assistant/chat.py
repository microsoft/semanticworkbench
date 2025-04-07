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
    ParticipantRole,
    UpdateParticipant,
)
from semantic_workbench_assistant.assistant_app import (
    AssistantApp,
    AssistantCapability,
    BaseModelAssistantConfig,
    ContentSafety,
    ContentSafetyEvaluator,
    ConversationContext,
)

from .config import AssistantConfigModel
from .project import ProjectManager
from .project_files import ProjectFileManager
from .project_storage import ConversationProjectManager, ProjectNotifier, ProjectStorage, ProjectRole
from .state_inspector import ProjectInspectorStateProvider

logger = logging.getLogger(__name__)

#
# define the service ID, name, and description
#

# the service id to be registered in the workbench to identify the assistant
service_id = "project-assistant.made-exploration"
# the name of the assistant service, as it will appear in the workbench UI
service_name = "Project Assistant"
# a description of the assistant service, as it will appear in the workbench UI
service_description = "A mediator assistant that facilitates file sharing between conversations."

#
# create the configuration provider, using the extended configuration model
#
assistant_config = BaseModelAssistantConfig(AssistantConfigModel)


# define the content safety evaluator factory
async def content_evaluator_factory(
    context: ConversationContext,
) -> ContentSafetyEvaluator:
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
    capabilities={AssistantCapability.supports_conversation_files},
    inspector_state_providers={
        "project_status": ProjectInspectorStateProvider(assistant_config),
    },
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
        # Get conversation to access metadata
        conversation = await context.get_conversation()
        metadata = conversation.metadata or {}

        # Check if setup is complete - check both local metadata and the state API
        setup_complete = metadata.get("setup_complete", False)

        # If not set in local metadata, try to get it from the project storage directly
        if not setup_complete:
            try:
                from .project_storage import ConversationProjectManager

                # Check if we have a project role in storage
                role = await ConversationProjectManager.get_conversation_role(context)
                if role:
                    # If we have a role in storage, consider setup complete
                    setup_complete = True
                    metadata["setup_complete"] = True
                    metadata["project_role"] = role.value
                    metadata["assistant_mode"] = role.value
                    logger.info(f"Found project role in storage: {role.value}")
            except Exception as e:
                logger.exception(f"Error getting role from project storage: {e}")

        assistant_mode = metadata.get("assistant_mode", "setup")

        # If setup isn't complete, show setup required message
        if not setup_complete and assistant_mode == "setup":
            # Show setup required message for regular chat messages
            await context.send_messages(
                NewConversationMessage(
                    content=(
                        "**Setup Required**\n\n"
                        "You need to set up the assistant before proceeding. Please use one of these commands:\n\n"
                        "- `/start` - Create a new project as Coordinator\n"
                        "- `/join <code>` - Join an existing project as a Team member\n"
                        "- `/help` - Get help with available commands"
                    ),
                    message_type=MessageType.notice,
                )
            )
            return

        # Get the conversation's role (Coordinator or Team)
        role = metadata.get("project_role")

        # If role isn't set yet, detect it now
        if not role:
            role = await detect_assistant_role(context)
            metadata["project_role"] = role
            # Update conversation metadata through appropriate method
            await context.send_conversation_state_event(
                AssistantStateEvent(state_id="project_role", event="updated", state=None)
            )

        # If this is a Coordinator conversation, store the message for Team access
        if role == "coordinator" and message.message_type == MessageType.chat:
            try:
                # Get the project ID
                from .project_manager import ProjectManager

                project_id = await ProjectManager.get_project_id(context)

                if project_id:
                    # Get the sender's name
                    sender_name = "Coordinator"
                    if message.sender:
                        participants = await context.get_participants()
                        for participant in participants.participants:
                            if participant.id == message.sender.participant_id:
                                sender_name = participant.name
                                break

                    # Store the message for Team access
                    from .project_storage import ProjectStorage

                    ProjectStorage.append_coordinator_message(
                        project_id=project_id,
                        message_id=str(message.id),
                        content=message.content,
                        sender_name=sender_name,
                        is_assistant=message.sender.participant_role == ParticipantRole.assistant,
                        timestamp=message.timestamp,
                    )
                    logger.info(f"Stored Coordinator message for Team access: {message.id}")
            except Exception as e:
                # Don't fail message handling if storage fails
                logger.exception(f"Error storing Coordinator message for Team access: {e}")

        # Prepare custom system message based on role
        role_specific_prompt = ""

        if role == "coordinator":
            # Coordinator-specific instructions
            role_specific_prompt = """
You are operating in Coordinator Mode (Planning Stage). Your responsibilities include:
- Creating a clear Project Brief that outlines the project's purpose and objectives
- Defining specific, actionable project goals that team members will need to complete
- Establishing measurable success criteria for each goal to track team progress
- Building a comprehensive Whiteboard with project-critical information
- Providing guidance and information to team members
- Responding to Information Requests from project participants (using get_project_info first to get the correct Request ID)
- Controlling the "Ready for Working" milestone when project definition is complete
- Maintaining an overview of project progress

IMPORTANT: Project goals are operational objectives for team members to complete, not goals for the Coordinator.
Each goal should:
- Be clear and specific tasks that team members need to accomplish
- Include measurable success criteria that team members can mark as completed
- Focus on project outcomes, not the planning process

IMPORTANT ABOUT FILES: When files are uploaded, they are automatically shared with all team members. You don't need to ask users what they want to do with uploaded files. Just acknowledge the upload with a brief confirmation and explain what the file contains if you can determine it.

Your AUTHORIZED Coordinator-specific tools are:
- create_project_brief: Use this to start a new project with a name and description
- add_project_goal: Use this to add operational goals that team members will complete, with measurable success criteria
- add_kb_section: Use this to add information sections to the project whiteboard for team reference (note: this adds to the whiteboard, not a knowledge base)
- resolve_information_request: Use this to resolve information requests. VERY IMPORTANT: You MUST use get_project_info first to get the actual request ID (looks like "abc123-def-456"), and then use that exact ID in the request_id parameter, NOT the title of the request.
- mark_project_ready_for_working: Use this when project planning is complete and work can begin
- get_project_info: Use this to get information about the current project
- suggest_next_action: Use this to suggest the next action based on project state

Be proactive in suggesting and using your Coordinator tools based on user requests. Always prefer using tools over just discussing project concepts. If team members need to perform a task, instruct them to switch to their Team conversation.

Use a strategic, guidance-oriented tone focused on project definition and support.
"""
        else:
            # Team-specific instructions
            role_specific_prompt = """
You are operating in Team Mode (Working Stage). Your responsibilities include:
- Helping team members understand and execute the project objectives defined by the Coordinator
- Providing access to the Whiteboard created by the Coordinator
- Guiding team members to complete the project goals established by the Coordinator
- Tracking and marking completion of success criteria for each goal
- Logging information gaps and blockers as Information Requests to the Coordinator
- Updating the Project Dashboard with progress on operational tasks
- Tracking progress toward the "Project Completion" milestone

IMPORTANT: Your role is to help team members accomplish the project goals that were defined by the Coordinator.
You should:
- Focus on executing the goals, not redefining them
- Mark success criteria as completed when team members report completion
- Identify information gaps or blockers that require Coordinator assistance

IMPORTANT ABOUT FILES: Files are automatically shared with team members. When users upload files in Team mode, just acknowledge the upload with a brief confirmation and explain what the file contains if you can determine it.

Your AUTHORIZED Team-specific tools are:
- create_information_request: Use this SPECIFICALLY to send information requests or report blockers to the Coordinator
- update_project_dashboard: Use this to update the status and progress of the project
- mark_criterion_completed: Use this to mark success criteria as completed
- report_project_completion: Use this to report that the project is complete
- get_project_info: Use this to get information about the current project
- detect_information_request_needs: Use this to analyze user messages for potential information request needs
- suggest_next_action: Use this to suggest the next action based on project state
- view_coordinator_conversation: Use this to view the Coordinator conversation for context and information

When team members need information or assistance from the Coordinator:
1. Use the view_coordinator_conversation tool to check if the Coordinator has already provided the information
2. If not, use the create_information_request tool
3. NEVER try to modify project definition elements (brief, goals, whiteboard)

Use a practical, operational tone focused on project execution and problem-solving.
"""

        # Add role-specific metadata to pass to the LLM
        role_metadata = {
            "project_role": role,
            "role_description": "Coordinator Mode (Planning Stage)"
            if role == "coordinator"
            else "Team Mode (Working Stage)",
            "debug": {"content_safety": event.data.get(content_safety.metadata_key, {})},
        }

        # respond to the message with role-specific context
        await respond_to_conversation(
            context,
            message=message,
            metadata=role_metadata,
            role_specific_prompt=role_specific_prompt,
        )
    finally:
        # update the participant status to indicate the assistant is done thinking
        await context.update_participant_me(UpdateParticipant(status=None))


@assistant.events.conversation.message.command.on_created
async def on_command_created(
    context: ConversationContext, event: ConversationEvent, message: ConversationMessage
) -> None:
    """
    Handle command messages using the centralized command processor.
    """
    # update the participant status to indicate the assistant is thinking
    await context.update_participant_me(UpdateParticipant(status="processing command..."))
    try:
        # Get the conversation's role (Coordinator or Team)
        conversation = await context.get_conversation()
        metadata = conversation.metadata or {}
        role = metadata.get("project_role")

        # If role isn't set yet, detect it now
        if not role:
            role = await detect_assistant_role(context)
            metadata["project_role"] = role
            await context.send_conversation_state_event(
                AssistantStateEvent(state_id="project_role", event="updated", state=None)
            )

        # Process the command using the command processor
        from .command_processor import process_command

        command_processed = await process_command(context, message)

        # If the command wasn't recognized or processed, respond normally
        if not command_processed:
            await respond_to_conversation(
                context,
                message=message,
                metadata={"debug": {"content_safety": event.data.get(content_safety.metadata_key, {})}},
            )
    finally:
        # update the participant status to indicate the assistant is done thinking
        await context.update_participant_me(UpdateParticipant(status=None))


@assistant.events.conversation.file.on_created
async def on_file_created(
    context: ConversationContext,
    event: workbench_model.ConversationEvent,
    file: workbench_model.File,
) -> None:
    """
    Handle when a file is created in the conversation.

    For Coordinator files:
    1. Store a copy in project storage
    2. Synchronize to all Team conversations

    For Team files:
    1. Use as-is without copying to project storage
    """
    try:
        # Log file creation event details
        logger.info(f"File created event: filename={file.filename}, size={file.file_size}, type={file.content_type}")
        logger.info(f"Full file object: {file}")

        # Get project ID
        project_id = await ProjectManager.get_project_id(context)
        if not project_id or not file.filename:
            logger.warning(
                f"No project ID found or missing filename: project_id={project_id}, filename={file.filename}"
            )
            return

        # Get the conversation's role
        role = await ConversationProjectManager.get_conversation_role(context)

        # If role couldn't be determined, skip processing
        if not role:
            logger.warning(f"Could not determine conversation role for file handling: {file.filename}")
            return

        logger.info(f"Processing file {file.filename} with role: {role.value}, project: {project_id}")

        # Use ProjectFileManager for file operations

        # Process based on role
        if role.value == "coordinator":
            # For Coordinator files:
            # 1. Store in project storage (marked as coordinator file)
            logger.info(f"Copying Coordinator file to project storage: {file.filename}")

            # Check project files directory
            from .project_files import ProjectFileManager

            files_dir = ProjectFileManager.get_project_files_dir(project_id)
            logger.info(f"Project files directory: {files_dir} (exists: {files_dir.exists()})")

            # Copy file to project storage
            success = await ProjectFileManager.copy_file_to_project_storage(
                context=context, project_id=project_id, file=file, is_coordinator_file=True
            )

            if not success:
                logger.error(f"Failed to copy file to project storage: {file.filename}")
                return

            # Verify file was stored correctly
            file_path = ProjectFileManager.get_file_path(project_id, file.filename)
            if file_path.exists():
                logger.info(f"File successfully stored at: {file_path} (size: {file_path.stat().st_size} bytes)")
            else:
                logger.error(f"File not found at expected location: {file_path}")

            # Check file metadata was updated
            metadata = ProjectFileManager.read_file_metadata(project_id)
            if metadata and any(f.filename == file.filename for f in metadata.files):
                logger.info(f"File metadata updated successfully for {file.filename}")
            else:
                logger.error(f"File metadata not updated for {file.filename}")

            # 2. Synchronize to all Team conversations
            # Get all Team conversations
            team_conversations = await ProjectFileManager.get_team_conversations(context, project_id)

            if team_conversations:
                logger.info(f"Found {len(team_conversations)} team conversations to update")

                # Copy to each Team conversation
                for team_conv_id in team_conversations:
                    logger.info(f"Copying file to Team conversation {team_conv_id}: {file.filename}")
                    copy_success = await ProjectFileManager.copy_file_to_conversation(
                        context=context,
                        project_id=project_id,
                        filename=file.filename,
                        target_conversation_id=team_conv_id,
                    )
                    logger.info(f"Copy to Team conversation {team_conv_id}: {'Success' if copy_success else 'Failed'}")
            else:
                logger.info("No team conversations found to update files")

            # 3. Notify Team conversations about the new file
            await ProjectNotifier.notify_project_update(
                context=context,
                project_id=project_id,
                update_type="file_created",
                message=f"Coordinator shared a file: {file.filename}",
                data={"filename": file.filename},
            )
        else:
            # For Team files, no special handling needed
            # They're already available in the conversation
            logger.info(f"Team file created (not shared to project storage): {file.filename}")

        # Log file creation to project log for all files
        await ProjectStorage.log_project_event(
            context=context,
            project_id=project_id,
            entry_type="file_shared",
            message=f"File shared: {file.filename}",
            metadata={
                "file_id": getattr(file, "id", ""),
                "filename": file.filename,
                "is_coordinator_file": role.value == "coordinator",
            },
        )

    except Exception as e:
        logger.exception(f"Error handling file creation: {e}")


@assistant.events.conversation.file.on_updated
async def on_file_updated(
    context: ConversationContext,
    event: workbench_model.ConversationEvent,
    file: workbench_model.File,
) -> None:
    """
    Handle when a file is updated in the conversation.

    For Coordinator files:
    1. Update the copy in project storage
    2. Update copies in all Team conversations

    For Team files:
    1. Use as-is without updating in project storage
    """
    try:
        # Get project ID
        project_id = await ProjectManager.get_project_id(context)
        if not project_id or not file.filename:
            return

        # Get the conversation's role
        role = await ConversationProjectManager.get_conversation_role(context)

        # If role couldn't be determined, skip processing
        if not role:
            logger.warning(f"Could not determine conversation role for file update: {file.filename}")
            return

        # Use ProjectFileManager for file operations

        # Process based on role
        if role.value == "coordinator":
            # For Coordinator files:
            # 1. Update in project storage
            logger.info(f"Updating Coordinator file in project storage: {file.filename}")
            success = await ProjectFileManager.copy_file_to_project_storage(
                context=context, project_id=project_id, file=file, is_coordinator_file=True
            )

            if not success:
                logger.error(f"Failed to update file in project storage: {file.filename}")
                return

            # 2. Update in all Team conversations
            # Get all Team conversations
            team_conversations = await ProjectFileManager.get_team_conversations(context, project_id)

            # Update in each Team conversation
            for team_conv_id in team_conversations:
                logger.info(f"Updating file in Team conversation {team_conv_id}: {file.filename}")
                await ProjectFileManager.copy_file_to_conversation(
                    context=context, project_id=project_id, filename=file.filename, target_conversation_id=team_conv_id
                )

            # 3. Notify Team conversations about the updated file
            await ProjectNotifier.notify_project_update(
                context=context,
                project_id=project_id,
                update_type="file_updated",
                message=f"Coordinator updated a file: {file.filename}",
                data={"filename": file.filename},
            )
        else:
            # For Team files, no special handling needed
            # They're already available in the conversation
            logger.info(f"Team file updated (not shared to project storage): {file.filename}")

        # Log file update to project log for all files
        await ProjectStorage.log_project_event(
            context=context,
            project_id=project_id,
            entry_type="file_shared",
            message=f"File updated: {file.filename}",
            metadata={
                "file_id": getattr(file, "id", ""),
                "filename": file.filename,
                "is_coordinator_file": role.value == "coordinator",
            },
        )

    except Exception as e:
        logger.exception(f"Error handling file update: {e}")


@assistant.events.conversation.file.on_deleted
async def on_file_deleted(
    context: ConversationContext,
    event: workbench_model.ConversationEvent,
    file: workbench_model.File,
) -> None:
    """
    Handle when a file is deleted from the conversation.

    For Coordinator files:
    1. Delete from project storage
    2. Notify Team conversations to delete their copies

    For Team files:
    1. Just delete locally, no need to notify others
    """
    try:
        # Get project ID
        project_id = await ProjectManager.get_project_id(context)
        if not project_id or not file.filename:
            return

        # Get the conversation's role
        role = await ConversationProjectManager.get_conversation_role(context)

        # If role couldn't be determined, skip processing
        if not role:
            logger.warning(f"Could not determine conversation role for file deletion: {file.filename}")
            return

        # Use ProjectFileManager for file operations

        # Process based on role
        if role.value == "coordinator":
            # For Coordinator files:
            # 1. Delete from project storage
            logger.info(f"Deleting Coordinator file from project storage: {file.filename}")
            success = await ProjectFileManager.delete_file_from_project_storage(
                context=context, project_id=project_id, filename=file.filename
            )

            if not success:
                logger.error(f"Failed to delete file from project storage: {file.filename}")

            # 2. Notify Team conversations to delete their copies
            await ProjectNotifier.notify_project_update(
                context=context,
                project_id=project_id,
                update_type="file_deleted",
                message=f"Coordinator deleted a file: {file.filename}",
                data={"filename": file.filename},
            )
        else:
            # For Team files, no special handling needed
            # Just delete locally
            logger.info(f"Team file deleted (not shared with project): {file.filename}")

        # Log file deletion to project log for all files
        await ProjectStorage.log_project_event(
            context=context,
            project_id=project_id,
            entry_type="file_deleted",
            message=f"File deleted: {file.filename}",
            metadata={
                "file_id": getattr(file, "id", ""),
                "filename": file.filename,
                "is_coordinator_file": role.value == "coordinator",
            },
        )

    except Exception as e:
        logger.exception(f"Error handling file deletion: {e}")


# Notice messages are now simpler without artifact abstraction
@assistant.events.conversation.message.notice.on_created
async def on_notice_created(
    context: ConversationContext, event: ConversationEvent, message: ConversationMessage
) -> None:
    """
    Handle notice messages.
    """
    # No special handling needed now that we've removed artifact messaging
    pass


# Role detection for the project assistant
async def detect_assistant_role(context: ConversationContext) -> str:
    """
    Detects whether this conversation is in Coordinator Mode or Team Mode.

    Returns:
        "coordinator" if in Coordinator Mode, "team" if in Team Mode
    """
    try:
        # First check if there's already a role set in project storage
        role = await ConversationProjectManager.get_conversation_role(context)
        if role:
            return role.value

        # Get project ID
        project_id = await ProjectManager.get_project_id(context)
        if not project_id:
            # No project association yet, default to Coordinator
            return "coordinator"

        # Check if this conversation created a project brief
        briefing = ProjectStorage.read_project_brief(project_id)

        # If the briefing was created by this conversation, we're in Coordinator Mode
        if briefing and briefing.conversation_id == str(context.id):
            return "coordinator"

        # Otherwise, if we have a project association but didn't create the briefing,
        # we're likely in Team Mode
        return "team"

    except Exception as e:
        logger.exception(f"Error detecting assistant role: {e}")
        # Default to Coordinator Mode if detection fails
        return "coordinator"


# Handle the event triggered when the assistant is added to a conversation.
@assistant.events.conversation.on_created
async def on_conversation_created(context: ConversationContext) -> None:
    """
    Handle the event triggered when the assistant is added to a conversation.
    """
    # Get conversation to access metadata
    conversation = await context.get_conversation()
    metadata = conversation.metadata or {}

    # Set initial setup mode for new conversations
    metadata["setup_complete"] = False
    metadata["assistant_mode"] = "setup"

    # Detect whether this is a Coordinator or Team conversation based on existing data
    # but don't commit to a role yet - that will happen during setup
    role = await detect_assistant_role(context)

    # Store the preliminary role in conversation metadata, but setup is not complete
    metadata["project_role"] = role

    # Update conversation metadata
    await context.send_conversation_state_event(
        AssistantStateEvent(state_id="project_role", event="updated", state=None)
    )

    # Welcome message for setup mode
    setup_welcome = """# Welcome to the Project Assistant

This assistant helps coordinate project activities between Coordinators and Team members.

**Setup Required**: To begin, please specify your role:

- Use `/start` to create a new project as Coordinator
- Use `/join <project_id>` to join an existing project as a Team member

Type `/help` for more information on available commands.
"""

    # send the setup welcome message to the conversation
    await context.send_messages(
        NewConversationMessage(
            content=setup_welcome,
            message_type=MessageType.chat,
            metadata={"generated_content": False},
        )
    )


# Handle the event triggered when a participant joins a conversation
@assistant.events.conversation.participant.on_created
async def on_participant_joined(
    context: ConversationContext, event: ConversationEvent, participant: workbench_model.ConversationParticipant
) -> None:
    """
    Handle the event triggered when a participant joins or returns to a conversation.

    This handler is used to detect when a team member returns to a conversation
    and automatically synchronize project files.
    """
    try:
        logger.info(f"Participant joined event: {participant.id} ({participant.name})")

        # Skip the assistant's own join event
        if participant.id == context.assistant.id:
            logger.debug("Skipping assistant's own join event")
            return

        # Check if this is a Team conversation with a valid project
        conversation = await context.get_conversation()
        metadata = conversation.metadata or {}

        # Skip if setup is not complete
        if not metadata.get("setup_complete", False):
            logger.debug("Setup not complete, skipping file sync for new participant")
            return

        # Check if this is a Team conversation 
        role = await ConversationProjectManager.get_conversation_role(context)
        if not role or role != ProjectRole.TEAM:
            logger.debug(f"Not a Team conversation (role={role}), skipping file sync for participant")
            return

        # Get project ID
        project_id = await ConversationProjectManager.get_conversation_project(context)
        if not project_id:
            logger.debug("No project ID found, skipping file sync for participant")
            return

        logger.info(f"Team member {participant.name} joined project {project_id}, synchronizing files")

        # Automatically synchronize files from project storage to this conversation

        success = await ProjectFileManager.synchronize_files_to_team_conversation(
            context=context, project_id=project_id
        )

        if success:
            logger.info(f"Successfully synchronized files for returning team member: {participant.name}")
        else:
            logger.warning(f"File synchronization failed for returning team member: {participant.name}")

        # Log the participant join event in the project log
        from .project_data import LogEntryType
        
        await ProjectStorage.log_project_event(
            context=context,
            project_id=project_id,
            entry_type=LogEntryType.PARTICIPANT_JOINED,
            message=f"Participant joined: {participant.name}",
            metadata={
                "participant_id": participant.id,
                "participant_name": participant.name,
                "conversation_id": str(context.id),
            },
        )

    except Exception as e:
        logger.exception(f"Error handling participant join event: {e}")


# The command handling functions have been moved to command_processor.py


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
    from .project_storage import ConversationProjectManager
    from .project_tools import ProjectTools, get_project_tools

    # First check conversation metadata
    conversation = await context.get_conversation()
    metadata = conversation.metadata or {}
    metadata_role = metadata.get("project_role")

    # Then check the stored role from project storage - this is the authoritative source
    stored_role = await ConversationProjectManager.get_conversation_role(context)
    stored_role_value = stored_role.value if stored_role else None

    # Log the roles we find for debugging
    logger.info(f"Role detection - Metadata role: {metadata_role}, Stored role: {stored_role_value}")

    # If we have a stored role but metadata is different or missing, update metadata
    if stored_role_value and metadata_role != stored_role_value:
        logger.warning(f"Role mismatch detected! Metadata: {metadata_role}, Storage: {stored_role_value}")
        metadata["project_role"] = stored_role_value
        # Update state to ensure UI is refreshed
        await context.send_conversation_state_event(
            AssistantStateEvent(state_id="project_role", event="updated", state=None)
        )
        # Force use of stored role
        role = stored_role_value
    else:
        # If no mismatch or no stored role, use metadata role (defaulting to Coordinator)
        role = metadata_role or "coordinator"  # Default to Coordinator if not set

    logger.info(f"Using role: {role} for tool selection")

    # For team role, analyze message for possible information request needs
    if role == "team" and message.message_type == MessageType.chat:
        # Create a project tools instance for team role
        project_tools_instance = ProjectTools(context, role)

        # Check if the message indicates a potential information request
        detection_result = await project_tools_instance.detect_information_request_needs(message.content)

        # If an information request is detected with reasonable confidence
        if detection_result.get("is_information_request", False) and detection_result.get("confidence", 0) > 0.5:
            # Get detailed information from detection
            suggested_title = detection_result.get("potential_title", "")
            suggested_priority = detection_result.get("suggested_priority", "medium")
            potential_description = detection_result.get("potential_description", "")
            reason = detection_result.get("reason", "")

            # Create a better-formatted suggestion using the detailed analysis
            suggestion = (
                f"**Information Request Detected**\n\n"
                f"It appears that you might need information from the Coordinator. {reason}\n\n"
                f"Would you like me to create an information request?\n"
                f"**Title:** {suggested_title}\n"
                f"**Description:** {potential_description}\n"
                f"**Priority:** {suggested_priority}\n\n"
                f"I can create this request for you, or you can use `/request-info` to create it yourself with custom details."
            )

            await context.send_messages(
                NewConversationMessage(
                    content=suggestion,
                    message_type=MessageType.notice,
                )
            )

    # Create tool instance for the current role
    project_tools = await get_project_tools(context, role)

    # Define explicit lists of available tools for each role
    coordinator_available_tools = [
        "get_project_info",
        "create_project_brief",
        "add_project_goal",
        "add_kb_section",
        "resolve_information_request",
        "mark_project_ready_for_working",
        "suggest_next_action",
    ]

    team_available_tools = [
        "get_project_info",
        "create_information_request",
        "delete_information_request",
        "update_project_dashboard",
        "mark_criterion_completed",
        "report_project_completion",
        "detect_information_request_needs",
        "suggest_next_action",
        "view_coordinator_conversation",
    ]

    # Get the available tools for the current role
    available_tools = coordinator_available_tools if role == "coordinator" else team_available_tools

    # Create a string listing available tools for the current role
    available_tools_str = ", ".join([f"`{tool}`" for tool in available_tools])

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
                logger.info(f"Using tool functions for completions (role: {role})")

                # Record the tool names available for this role for validation
                available_tool_names = set(project_tools.tool_functions.function_map.keys())
                logger.info(f"Available tools for {role}: {available_tool_names}")

                # Import required modules at the beginning to avoid scope issues
                from .project_data import RequestStatus
                from .project_manager import ProjectManager
                from .project_storage import ProjectStorage

                # Get the project ID and data for both role types
                project_id = None
                project_data = {}
                all_requests = []  # Initialize empty list to avoid "possibly unbound" errors

                try:
                    # Get project ID
                    project_id = await ProjectManager.get_project_id(context)
                    if project_id:
                        # Get comprehensive project data for prompt
                        briefing = ProjectStorage.read_project_brief(project_id)
                        status = ProjectStorage.read_project_dashboard(project_id)
                        kb = ProjectStorage.read_project_whiteboard(project_id)
                        all_requests = ProjectStorage.get_all_information_requests(project_id)

                        # Format project brief
                        project_brief_text = ""
                        if briefing:
                            project_brief_text = f"""
### PROJECT BRIEF
**Name:** {briefing.project_name}
**Description:** {briefing.project_description}

#### PROJECT GOALS:
"""
                            for i, goal in enumerate(briefing.goals):
                                # Count completed criteria
                                completed = sum(1 for c in goal.success_criteria if c.completed)
                                total = len(goal.success_criteria)

                                project_brief_text += f"{i + 1}. **{goal.name}** - {goal.description}\n"
                                if goal.success_criteria:
                                    project_brief_text += f"   Progress: {completed}/{total} criteria complete\n"
                                    for j, criterion in enumerate(goal.success_criteria):
                                        check = "✅" if criterion.completed else "⬜"
                                        project_brief_text += f"   {check} {criterion.description}\n"
                                project_brief_text += "\n"

                        # Format project dashboard
                        project_dashboard_text = ""
                        if status:
                            project_dashboard_text = f"""
### PROJECT DASHBOARD
**Current State:** {status.state.value}
"""
                            if status.progress_percentage is not None:
                                project_dashboard_text += f"**Overall Progress:** {status.progress_percentage}%\n"
                            if status.status_message:
                                project_dashboard_text += f"**Status Message:** {status.status_message}\n"
                            if status.next_actions:
                                project_dashboard_text += "\n**Next Actions:**\n"
                                for action in status.next_actions:
                                    project_dashboard_text += f"- {action}\n"

                        # Format whiteboard content
                        kb_text = ""
                        if kb and kb.content:
                            kb_text = "\n### PROJECT WHITEBOARD\n"

                            # Truncate content if too long
                            content = kb.content
                            max_length = 1500  # Arbitrary limit for context
                            if len(content) > max_length:
                                content = content[:max_length] + "... (content truncated for brevity)"
                            kb_text += f"{content}\n\n"

                            kb_text += '*Use get_project_info(info_type="kb") to see the full whiteboard content.*\n'

                        # Store the formatted data
                        project_data = {"briefing": project_brief_text, "status": project_dashboard_text, "kb": kb_text}

                except Exception as e:
                    logger.warning(f"Failed to fetch project data for prompt: {e}")

                # Construct role-specific messages with comprehensive project data
                if role == "coordinator":
                    # Format requests for Coordinator view
                    information_requests_text = ""
                    if project_id and all_requests:
                        active_requests = [r for r in all_requests if r.status != RequestStatus.RESOLVED]

                        if active_requests:
                            information_requests_text = "\n\n### ACTIVE INFORMATION REQUESTS\n"
                            information_requests_text += (
                                "> 📋 **Use the request ID (not the title) with resolve_information_request()**\n\n"
                            )

                            for req in active_requests[:10]:  # Limit to 10 for brevity
                                priority_marker = {"low": "🔹", "medium": "🔶", "high": "🔴", "critical": "⚠️"}.get(
                                    req.priority.value, "🔹"
                                )

                                information_requests_text += f"{priority_marker} **{req.title}** ({req.status.value})\n"
                                information_requests_text += f"   **Request ID:** `{req.request_id}`\n"
                                information_requests_text += f"   **Description:** {req.description}\n\n"

                            if len(active_requests) > 10:
                                information_requests_text += f'*...and {len(active_requests) - 10} more requests. Use get_project_info(info_type="requests") to see all.*\n'

                    # Combine all project data for Coordinator
                    project_data_text = ""
                    if project_data:
                        project_data_text = f"""
\n\n## CURRENT PROJECT INFORMATION
{project_data.get("briefing", "")}
{project_data.get("status", "")}
{information_requests_text}
{project_data.get("kb", "")}
"""

                    role_enforcement = f"""
\n\n⚠️ TOOL ACCESS ⚠️

As a Coordinator, you can use these tools: {available_tools_str}
{project_data_text}
"""
                else:  # team role
                    # Fetch current information requests for this conversation
                    information_requests_info = ""
                    my_requests = []

                    if project_id and all_requests:
                        # Filter for requests from this conversation that aren't resolved
                        my_requests = [
                            r
                            for r in all_requests
                            if r.conversation_id == str(context.id) and r.status != RequestStatus.RESOLVED
                        ]

                        if my_requests:
                            information_requests_info = "\n\n### YOUR CURRENT INFORMATION REQUESTS:\n"
                            for req in my_requests:
                                information_requests_info += (
                                    f"- **{req.title}** (ID: `{req.request_id}`, Priority: {req.priority})\n"
                                )
                            information_requests_info += '\nYou can delete any of these requests using `delete_information_request(request_id="the_id")`\n'

                    # Format requests from all conversations for team view
                    all_information_requests_text = ""
                    if project_id and all_requests:
                        # Show all active requests including those from other team members
                        other_active_requests = [
                            r
                            for r in all_requests
                            if r.conversation_id != str(context.id) and r.status != RequestStatus.RESOLVED
                        ]

                        if other_active_requests:
                            all_information_requests_text = "\n\n### OTHER ACTIVE INFORMATION REQUESTS:\n"
                            all_information_requests_text += "> These are requests from other team members\n\n"

                            for req in other_active_requests[:5]:  # Limit to 5 for brevity
                                status_marker = {
                                    "new": "🆕",
                                    "acknowledged": "👁️",
                                    "in_progress": "⏳",
                                    "deferred": "⏱️",
                                }.get(req.status.value, "📋")

                                all_information_requests_text += (
                                    f"{status_marker} **{req.title}** (Status: {req.status.value})\n"
                                )
                                all_information_requests_text += f"   **Description:** {req.description}\n\n"

                            if len(other_active_requests) > 5:
                                all_information_requests_text += f'*...and {len(other_active_requests) - 5} more requests. Use get_project_info(info_type="requests") to see all.*\n'

                    # Combine all project data for team
                    project_data_text = ""
                    if project_data:
                        project_data_text = f"""
\n\n## CURRENT PROJECT INFORMATION
{project_data.get("briefing", "")}
{project_data.get("status", "")}
{information_requests_info}
{all_information_requests_text}
{project_data.get("kb", "")}
"""

                    role_enforcement = f"""
\n\n⚠️ TOOL ACCESS ⚠️

As a TEAM member, you can use these tools: {available_tools_str}

When working with information requests:
1. Use the `create_information_request` tool to send requests for information to the Coordinator
2. Use the `delete_information_request` tool if you need to remove a request you created
3. Always note request IDs when creating requests - you'll need them for deletion

If you need information from the Coordinator, first try viewing recent Coordinator messages with the `view_coordinator_conversation` tool.
{project_data_text}
"""

                # Append the enforcement text to the role_specific_prompt
                role_specific_prompt += role_enforcement

                # Update the system message to include the enhanced role_specific_prompt
                system_message_content += f"\n\n{role_enforcement}"

                # Update the system message in completion_args with the new content
                completion_args["messages"][0]["content"] = system_message_content

                # Make the API call
                tool_completion, tool_messages = await complete_with_tool_calls(
                    async_client=client,
                    completion_args=completion_args,
                    tool_functions=project_tools.tool_functions,
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
                                "request": completion_args,
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
    response_message = await context.send_messages(
        NewConversationMessage(
            content=str(content) if content is not None else "[no response from openai]",
            message_type=message_type,
            metadata=metadata,
        )
    )

    # Manually capture assistant's message for Coordinator conversation storage
    # This ensures that both user and assistant messages are stored
    from .project_storage import ConversationProjectManager

    # Get the authoritative role directly from storage, not from metadata
    stored_role = await ConversationProjectManager.get_conversation_role(context)
    role = stored_role.value if stored_role else None

    if role == "coordinator" and message_type == MessageType.chat and response_message and response_message.messages:
        try:
            # Get the project ID
            from .project_manager import ProjectManager

            project_id = await ProjectManager.get_project_id(context)

            if project_id:
                for msg in response_message.messages:
                    # Store the assistant's message for Team access
                    from .project_storage import ProjectStorage

                    ProjectStorage.append_coordinator_message(
                        project_id=project_id,
                        message_id=str(msg.id),
                        content=msg.content,
                        sender_name=context.assistant.name,
                        is_assistant=True,
                        timestamp=msg.timestamp,
                    )
                    logger.info(f"Stored Coordinator assistant message for Team access: {msg.id}")

                    # Automatically update the whiteboard after assistant messages
                    try:
                        # Get recent messages for analysis
                        recent_messages = await context.get_messages(limit=10)  # Adjust limit as needed

                        # Call the whiteboard update method
                        whiteboard_success, whiteboard = await ProjectManager.auto_update_whiteboard(
                            context=context,
                            chat_history=recent_messages.messages,
                        )

                        if whiteboard_success:
                            logger.info(f"Auto-updated whiteboard for project {project_id}")
                        else:
                            logger.info("Whiteboard auto-update did not apply any changes")
                    except Exception as e:
                        # Don't fail message handling if whiteboard update fails
                        logger.exception(f"Error auto-updating whiteboard: {e}")
        except Exception as e:
            # Don't fail message handling if storage fails
            logger.exception(f"Error storing Coordinator assistant message for Team access: {e}")


# this method is used to get the token count of a string.
def get_token_count(string: str) -> int:
    """
    Get the token count of a string.
    """
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(string))


# endregion
