# Copyright (c) Microsoft. All rights reserved.

# Project Assistant implementation
#
# This assistant provides project coordination capabilities with Coordinator and Team member roles,
# supporting whiteboard sharing, file synchronization, and team collaboration.


import logging
import re
from typing import Any, List

import deepmerge
import openai_client
from assistant_extensions.attachments import AttachmentsExtension
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
    AssistantTemplate,
    BaseModelAssistantConfig,
    ContentSafety,
    ContentSafetyEvaluator,
    ConversationContext,
)

from .config import AssistantConfigModel, ContextTransferConfigModel
from .project_files import ProjectFileManager
from .project_manager import ProjectManager
from .project_storage import (
    ConversationProjectManager,
    ProjectNotifier,
    ProjectRole,
    ProjectStorage,
)
from .state_inspector import ProjectInspectorStateProvider

logger = logging.getLogger(__name__)

service_id = "project-assistant.made-exploration"
service_name = "Project Assistant"
service_description = "A mediator assistant that facilitates file sharing between conversations."

# Config.
assistant_config = BaseModelAssistantConfig(
    AssistantConfigModel,
    additional_templates={
        "context_transfer": ContextTransferConfigModel,
    },
)


# Content safety.
async def content_evaluator_factory(
    context: ConversationContext,
) -> ContentSafetyEvaluator:
    config = await assistant_config.get(context.assistant)
    return CombinedContentSafetyEvaluator(config.content_safety_config)


content_safety = ContentSafety(content_evaluator_factory)

# Set up the app.
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
    additional_templates=[
        AssistantTemplate(
            id="context_transfer",
            name="Context Transfer Assistant (experimental)",
            description="An assistant for capturing and sharing complex information for others to explore.",
        ),
    ],
)

attachments_extension = AttachmentsExtension(assistant)

app = assistant.fastapi_app()


@assistant.events.conversation.message.chat.on_created
async def on_message_created(
    context: ConversationContext, event: ConversationEvent, message: ConversationMessage
) -> None:
    """
    Handle user chat messages and provide appropriate project coordination responses.

    This manages project setup/detection, role enforcement, and updating the whiteboard
    for coordinator messages.
    """

    # update the participant status to indicate the assistant is thinking
    await context.update_participant_me(UpdateParticipant(status="thinking..."))
    try:
        # Get conversation to access metadata
        conversation = await context.get_conversation()
        metadata = conversation.metadata or {}

        # Check if setup is complete - check both local metadata and the state API
        setup_complete = metadata.get("setup_complete", False)

        # First check if project ID exists - if it does, setup should always be considered complete
        from .project_manager import ProjectManager

        project_id = await ProjectManager.get_project_id(context)
        if project_id:
            # If we have a project ID, we should never show the setup instructions
            setup_complete = True

            # If metadata doesn't reflect this, try to get actual role
            from .project_storage import ConversationProjectManager

            role = await ConversationProjectManager.get_conversation_role(context)
            if role:
                metadata["project_role"] = role.value
                metadata["assistant_mode"] = role.value
                metadata["setup_complete"] = True
                logger.info(f"Found project role in storage: {role.value}")

                # Update conversation metadata to fix this inconsistency
                await context.send_conversation_state_event(
                    AssistantStateEvent(state_id="setup_complete", event="updated", state=None)
                )
                await context.send_conversation_state_event(
                    AssistantStateEvent(state_id="project_role", event="updated", state=None)
                )
                await context.send_conversation_state_event(
                    AssistantStateEvent(state_id="assistant_mode", event="updated", state=None)
                )
            else:
                # Default to team if we can't determine
                metadata["project_role"] = "team"
                metadata["assistant_mode"] = "team"
                metadata["setup_complete"] = True
                logger.info("Could not determine role from storage, defaulting to team mode")
        # If no project ID, check storage as a fallback
        elif not setup_complete:
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

        # If setup isn't complete, show setup required message (only if we truly have no project)
        if not setup_complete and assistant_mode == "setup" and not project_id:
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
        from .utils import load_text_include

        role_specific_prompt = ""

        if role == "coordinator":
            # Coordinator-specific instructions
            role_specific_prompt = load_text_include("coordinator_prompt.txt")
        else:
            # Team-specific instructions
            role_specific_prompt = load_text_include("team_prompt.txt")

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
            attachments_extension=attachments_extension,
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
                attachments_extension=attachments_extension,
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
                context=context,
                project_id=project_id,
                file=file,
                is_coordinator_file=True,
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

            # 3. Update all UIs but don't send notifications to reduce noise
            await ProjectNotifier.notify_project_update(
                context=context,
                project_id=project_id,
                update_type="file_created",
                message=f"Coordinator shared a file: {file.filename}",
                data={"filename": file.filename},
                send_notification=False,  # Don't send notification to reduce noise
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
                context=context,
                project_id=project_id,
                file=file,
                is_coordinator_file=True,
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
                    context=context,
                    project_id=project_id,
                    filename=file.filename,
                    target_conversation_id=team_conv_id,
                )

            # 3. Update all UIs but don't send notifications to reduce noise
            await ProjectNotifier.notify_project_update(
                context=context,
                project_id=project_id,
                update_type="file_updated",
                message=f"Coordinator updated a file: {file.filename}",
                data={"filename": file.filename},
                send_notification=False,  # Don't send notification to reduce noise
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

            # 2. Update all UIs about the deletion but don't send notifications to reduce noise
            await ProjectNotifier.notify_project_update(
                context=context,
                project_id=project_id,
                update_type="file_deleted",
                message=f"Coordinator deleted a file: {file.filename}",
                data={"filename": file.filename},
                send_notification=False,  # Don't send notification to reduce noise
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


# Role detection for the project assistant
async def detect_assistant_role(context: ConversationContext) -> str:
    """
    Detects whether this conversation is in Coordinator Mode or Team Mode.

    Returns:
        "coordinator" if in Coordinator Mode, "team" if in Team Mode
    """
    try:
        # First check conversation metadata for role indicators
        conversation = await context.get_conversation()
        metadata = conversation.metadata or {}

        # Check if this is explicitly marked as a team workspace
        if metadata.get("is_team_workspace", False):
            logger.info("Detected role from metadata: team workspace")
            return "team"

        # Check if this was created through a share redemption
        share_redemption = metadata.get("share_redemption", {})
        if share_redemption and share_redemption.get("conversation_share_id"):
            # Check if the share metadata has project information
            share_metadata = share_redemption.get("metadata", {})
            if share_metadata.get("is_team_workspace", False) or share_metadata.get("project_id"):
                logger.info("Detected role from share redemption: team")
                return "team"

        # Next check if there's already a role set in project storage
        role = await ConversationProjectManager.get_conversation_role(context)
        if role:
            logger.info(f"Detected role from storage: {role.value}")
            return role.value

        # Get project ID
        project_id = await ProjectManager.get_project_id(context)
        if not project_id:
            # No project association yet, default to Coordinator
            logger.info("No project association, defaulting to coordinator")
            return "coordinator"

        # Check if this conversation created a project brief
        briefing = ProjectStorage.read_project_brief(project_id)

        # If the briefing was created by this conversation, we're in Coordinator Mode
        if briefing and briefing.conversation_id == str(context.id):
            logger.info("Detected role from briefing creation: coordinator")
            return "coordinator"

        # Otherwise, if we have a project association but didn't create the briefing,
        # we're likely in Team Mode
        logger.info("Detected role from project association: team")
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

    This handler now automatically:
    1. Checks if this is a new conversation or a shared team workspace
    2. For new conversations, creates a project and sets up as coordinator
    3. For shared conversations via share URL, sets up as team member
    4. Creates and stores share URL for team workspace
    """
    # Get conversation to access metadata
    conversation = await context.get_conversation()
    metadata = conversation.metadata or {}

    # Check if this is a team workspace created by a coordinator
    if metadata.get("is_team_workspace", False):
        # This is already a team workspace conversation
        logger.info("This is a team workspace conversation created by a coordinator")
        metadata["setup_complete"] = True
        metadata["assistant_mode"] = "team"
        metadata["project_role"] = "team"

        # Associate with the project ID if provided in metadata
        project_id = metadata.get("project_id")
        if project_id:
            # Set this conversation as a team member for the project
            await ConversationProjectManager.associate_conversation_with_project(context, project_id)
            await ConversationProjectManager.set_conversation_role(context, project_id, ProjectRole.TEAM)
            logger.info(f"Associated team workspace with project: {project_id}")

        # Update conversation metadata
        await context.send_conversation_state_event(
            AssistantStateEvent(state_id="setup_complete", event="updated", state=None)
        )
        await context.send_conversation_state_event(
            AssistantStateEvent(state_id="project_role", event="updated", state=None)
        )
        await context.send_conversation_state_event(
            AssistantStateEvent(state_id="assistant_mode", event="updated", state=None)
        )

        # Use welcome message from config
        config = await assistant_config.get(context.assistant)
        welcome_message = "# Welcome to the Team Workspace\n\nThis conversation is for collaboration on the project. All team members will use this shared space."

        # Send welcome message
        await context.send_messages(
            NewConversationMessage(
                content=welcome_message,
                message_type=MessageType.chat,
                metadata={"generated_content": False},
            )
        )
        return

    # Check if this is a conversation created through a share URL
    share_redemption = metadata.get("share_redemption", {})
    if share_redemption and share_redemption.get("conversation_share_id"):
        share_metadata = share_redemption.get("metadata", {})
        project_id = share_metadata.get("project_id")

        if project_id:
            # Set this conversation as a team member for the project
            await ConversationProjectManager.associate_conversation_with_project(context, project_id)
            await ConversationProjectManager.set_conversation_role(context, project_id, ProjectRole.TEAM)

            # Update conversation metadata
            metadata["setup_complete"] = True
            metadata["assistant_mode"] = "team"
            metadata["project_role"] = "team"

            await context.send_conversation_state_event(
                AssistantStateEvent(state_id="setup_complete", event="updated", state=None)
            )
            await context.send_conversation_state_event(
                AssistantStateEvent(state_id="project_role", event="updated", state=None)
            )
            await context.send_conversation_state_event(
                AssistantStateEvent(state_id="assistant_mode", event="updated", state=None)
            )

            # Use team welcome message
            config = await assistant_config.get(context.assistant)
            welcome_message = "# Welcome to the Team Workspace\n\nYou've joined this project as a team member. You can collaborate with the coordinator and other team members here."

            # Send welcome message
            await context.send_messages(
                NewConversationMessage(
                    content=welcome_message,
                    message_type=MessageType.chat,
                    metadata={"generated_content": False},
                )
            )
            return

    # This is a new conversation (not from a share and not a team workspace)
    # Automatically create a new project and set up as coordinator
    logger.info("Creating new project for coordinator conversation")

    # Create a new project
    success, project_id = await ProjectManager.create_project(context)

    if success and project_id:
        # Update conversation metadata
        metadata["setup_complete"] = True
        metadata["assistant_mode"] = "coordinator"
        metadata["project_role"] = "coordinator"

        await context.send_conversation_state_event(
            AssistantStateEvent(state_id="setup_complete", event="updated", state=None)
        )
        await context.send_conversation_state_event(
            AssistantStateEvent(state_id="project_role", event="updated", state=None)
        )
        await context.send_conversation_state_event(
            AssistantStateEvent(state_id="assistant_mode", event="updated", state=None)
        )

        # Create a default project brief with placeholder information
        await ProjectManager.create_project_brief(
            context=context,
            project_name="New Project",
            project_description="This project was automatically created. Please update the project brief with your project details.",
        )

        # Create a team workspace conversation and share URL
        (
            success,
            team_conversation_id,
            share_url,
        ) = await ProjectManager.create_team_conversation(
            context=context, project_id=project_id, project_name="New Project"
        )

        if success and share_url:
            # Store the team workspace information in the coordinator's metadata
            # Using None for state as required by the type system
            metadata["team_workspace_id"] = team_conversation_id
            metadata["team_workspace_share_url"] = share_url

            await context.send_conversation_state_event(
                AssistantStateEvent(state_id="team_workspace_id", event="updated", state=None)
            )

            await context.send_conversation_state_event(
                AssistantStateEvent(state_id="team_workspace_share_url", event="updated", state=None)
            )

            # Log the creation
            logger.info(f"Created team workspace: {team_conversation_id} with share URL: {share_url}")

            # Use coordinator welcome message with link
            config = await assistant_config.get(context.assistant)
            welcome_message = f"""# Welcome to the Project Assistant

This conversation is your personal workspace as the project coordinator.

**To invite team members to your project, copy and share this link with them:**
[Join Team Workspace]({share_url})

I've created a brief for your project. Let's start by updating it with your project goals and details."""
        else:
            # Use fallback welcome message without link
            config = await assistant_config.get(context.assistant)
            welcome_message = """# Welcome to the Project Assistant

This conversation is your personal workspace as the project coordinator. I'll help you set up and manage your project.

Let's start by updating the project brief with your goals and details."""
    else:
        # Failed to create project - use fallback mode
        metadata["setup_complete"] = False
        metadata["assistant_mode"] = "setup"

        # Use default welcome from config
        config = await assistant_config.get(context.assistant)
        welcome_message = config.welcome_message

    # Send the welcome message
    await context.send_messages(
        NewConversationMessage(
            content=welcome_message,
            message_type=MessageType.chat,
            metadata={"generated_content": False},
        )
    )


# Handle the event triggered when a participant joins a conversation
@assistant.events.conversation.participant.on_created
async def on_participant_joined(
    context: ConversationContext,
    event: ConversationEvent,
    participant: workbench_model.ConversationParticipant,
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
        project_id = await ConversationProjectManager.get_associated_project_id(context)
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


# OpenAI integration for message responses
#


async def respond_to_conversation(
    context: ConversationContext,
    message: ConversationMessage,
    attachments_extension: AttachmentsExtension,
    metadata: dict[str, Any] = {},
    role_specific_prompt: str = "",
) -> None:
    """
    Respond to a conversation message.
    """

    method_metadata_key = "respond_to_conversation"
    config = await assistant_config.get(context.assistant)
    participants_response = await context.get_participants(include_inactive=True)
    silence_token = "{{SILENCE}}"
    system_message_content = config.guardrails_prompt
    system_message_content += f'\n\n{config.instruction_prompt}\n\nYour name is "{context.assistant.name}".'
    if role_specific_prompt:
        system_message_content += f"\n\n{role_specific_prompt}"

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

    # Initialize message list with system message
    completion_messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": system_message_content,
        }
    ]

    # Calculate token count for the system message
    token_count = openai_client.num_tokens_from_messages(
        model=config.request_config.openai_model,
        messages=completion_messages,
    )

    # Format message helper function
    def format_message(message: ConversationMessage) -> str:
        """Consistent formatter that includes the participant name for multi-participant and name references"""
        conversation_participant = next(
            (
                participant
                for participant in participants_response.participants
                if participant.id == message.sender.participant_id
            ),
            None,
        )
        participant_name = conversation_participant.name if conversation_participant else "unknown"

        message_datetime = message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return f"[{participant_name} - {message_datetime}]: {message.content}"

    # Generate the attachment messages
    attachment_messages: List[ChatCompletionMessageParam] = openai_client.convert_from_completion_messages(
        await attachments_extension.get_completion_messages_for_attachments(
            context,
            config=config.attachments_config,
        )
    )

    # Add attachment messages to completion messages
    completion_messages.extend(attachment_messages)
    
    # Update token count to include attachment messages
    token_count += openai_client.num_tokens_from_messages(
        model=config.request_config.openai_model,
        messages=attachment_messages,
    )

    # Calculate available tokens for history messages
    available_tokens = config.request_config.max_tokens - config.request_config.response_tokens
    
    # Get the conversation history
    # For pagination, we'll retrieve messages in batches as needed
    history_messages: list[ChatCompletionMessageParam] = []
    before_message_id = message.id
    
    # Track token usage and overflow
    token_overage = 0
    
    # We'll fetch messages in batches until we hit the token limit or run out of messages
    while True:
        # Get a batch of messages
        messages_response = await context.get_messages(
            before=before_message_id,
            limit=100,  # Get messages in batches of 100
            message_types=[MessageType.chat]  # Include only chat messages
        )
        
        messages_list = messages_response.messages
        
        # If no messages found, break the loop
        if not messages_list or len(messages_list) == 0:
            break
            
        # Set before_message_id for the next batch
        before_message_id = messages_list[0].id
        
        # Process messages in reverse order (oldest first for history)
        for msg in reversed(messages_list):
            # Format this message for inclusion
            formatted_message = format_message(msg)
            
            # Create the message parameter based on sender with proper typing
            from openai.types.chat import (
                ChatCompletionAssistantMessageParam,
                ChatCompletionUserMessageParam
            )
            
            if msg.sender.participant_id == context.assistant.id:
                chat_message: ChatCompletionMessageParam = ChatCompletionAssistantMessageParam(
                    role="assistant",
                    content=formatted_message,
                )
            else:
                chat_message: ChatCompletionMessageParam = ChatCompletionUserMessageParam(
                    role="user",
                    content=formatted_message,
                )
                
            # Calculate tokens for this message
            message_tokens = openai_client.num_tokens_from_messages(
                model=config.request_config.openai_model,
                messages=[chat_message],
            )
            
            # Check if we can add this message without exceeding the token limit
            if token_overage == 0 and token_count + message_tokens < available_tokens:
                # Add message to the front of history_messages (to maintain chronological order)
                history_messages.insert(0, chat_message)
                token_count += message_tokens
            else:
                # We've exceeded the token limit, track the overage
                token_overage += message_tokens
        
        # If we've already exceeded the token limit, no need to fetch more messages
        if token_overage > 0:
            break
    
    # Log the token usage
    logger.debug(f"Token usage: {token_count}/{available_tokens} tokens used, {token_overage} tokens skipped")
    
    # Add history messages to completion messages
    completion_messages.extend(history_messages)
    
    # Final check to ensure we don't exceed the token limit
    total_token_count = openai_client.num_tokens_from_messages(
        model=config.request_config.openai_model,
        messages=completion_messages,
    )
    
    if total_token_count > available_tokens:
        logger.warning(
            f"Token limit exceeded: {total_token_count} > {available_tokens}. "
            f"Some conversation history has been truncated."
        )

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
                        whiteboard = ProjectStorage.read_project_whiteboard(project_id)
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
                        whiteboard_text = ""
                        if whiteboard and whiteboard.content:
                            whiteboard_text = "\n### PROJECT WHITEBOARD\n"

                            # Truncate content if too long
                            content = whiteboard.content
                            max_length = 1500  # Arbitrary limit for context
                            if len(content) > max_length:
                                content = content[:max_length] + "... (content truncated for brevity)"
                            whiteboard_text += f"{content}\n\n"

                            whiteboard_text += (
                                '*Use get_project_info(info_type="whiteboard") to see the full whiteboard content.*\n'
                            )

                        # Store the formatted data
                        project_data = {
                            "briefing": project_brief_text,
                            "status": project_dashboard_text,
                            "whiteboard": whiteboard_text,
                        }

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
                                priority_marker = {
                                    "low": "🔹",
                                    "medium": "🔶",
                                    "high": "🔴",
                                    "critical": "⚠️",
                                }.get(req.priority.value, "🔹")

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
{project_data.get("whiteboard", "")}
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
{project_data.get("whiteboard", "")}
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
                    # This will update the whiteboard content but won't send notifications to users
                    try:
                        # Get recent messages for analysis
                        recent_messages = await context.get_messages(limit=10)  # Adjust limit as needed

                        # Call the whiteboard update method - this is configured to NOT send notifications
                        # to avoid cluttering the UI with frequent update messages
                        (
                            whiteboard_success,
                            whiteboard,
                        ) = await ProjectManager.auto_update_whiteboard(
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


# endregion
