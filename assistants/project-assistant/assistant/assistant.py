# Copyright (c) Microsoft. All rights reserved.

# Project Assistant implementation

import asyncio
import pathlib
import re
from typing import TYPE_CHECKING, Any

from assistant_extensions import attachments, dashboard_card, navigator
from content_safety.evaluators import CombinedContentSafetyEvaluator
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
    ContentSafety,
    ContentSafetyEvaluator,
    ConversationContext,
)

if TYPE_CHECKING:
    pass

from .agentic import agentic
from .agentic.respond import (
    SILENCE_TOKEN,
    CoordinatorOutput,
    TeamOutput,
    respond_to_conversation,
)
from .config import assistant_config
from .data import ConversationRole, InspectorTab, LogEntryType
from .domain import ShareManager
from .files import ShareFilesManager
from .logging import logger
from .notifications import Notifications
from .ui_tabs import BriefInspector, DebugInspector, LearningInspector, SharingInspector
from .utils import (
    DEFAULT_TEMPLATE_ID,
    load_text_include,
)

service_id = "project-assistant.made-exploration"
service_name = "Project Assistant (KTA)"
service_description = "A mediator assistant that facilitates sharing knowledge between parties."


async def content_evaluator_factory(
    context: ConversationContext,
) -> ContentSafetyEvaluator:
    config = await assistant_config.get(context.assistant)
    return CombinedContentSafetyEvaluator(config.content_safety_config)


content_safety = ContentSafety(content_evaluator_factory)

assistant = AssistantApp(
    assistant_service_id=service_id,
    assistant_service_name=service_name,
    assistant_service_description=service_description,
    config_provider=assistant_config.provider,
    content_interceptor=content_safety,
    capabilities={AssistantCapability.supports_conversation_files},
    inspector_state_providers={
        InspectorTab.BRIEF: BriefInspector(assistant_config),
        InspectorTab.LEARNING: LearningInspector(assistant_config),
        InspectorTab.SHARING: SharingInspector(assistant_config),
        InspectorTab.DEBUG: DebugInspector(assistant_config),
    },
    assistant_service_metadata={
        **dashboard_card.metadata(
            dashboard_card.TemplateConfig(
                enabled=True,
                template_id=DEFAULT_TEMPLATE_ID,
                background_color="rgb(198, 177, 222)",
                icon=dashboard_card.image_to_url(
                    pathlib.Path(__file__).parent / "assets" / "icon-knowledge-transfer.svg",
                    "image/svg+xml",
                ),
                card_content=dashboard_card.CardContent(
                    content_type="text/markdown",
                    content=load_text_include("card_content.md"),
                ),
            ),
        ),
        **navigator.metadata_for_assistant_navigator({
            "default": load_text_include("assistant_info.md"),
        }),
    },
)

attachments_extension = attachments.AttachmentsExtension(assistant)

app = assistant.fastapi_app()


@assistant.events.conversation.on_created_including_mine
async def on_conversation_created(context: ConversationContext) -> None:
    """
    The assistant manages three types of conversations:
    1. Coordinator Conversation: The main conversation used by the knowledge coordinator
    2. Shareable Team Conversation: A template conversation that has a share URL and is never directly used
    3. Team Conversation(s): Individual conversations for team members created when they redeem the share URL
    """

    conversation = await context.get_conversation()

    # We can't pick up the role from the share data yet, so
    # we need to determine the role based on the conversation metadata.
    conversation_metadata = conversation.metadata or {}
    share_id = conversation_metadata.get("share_id")
    if not share_id:
        role = ConversationRole.COORDINATOR
    else:
        if conversation.imported_from_conversation_id:
            role = ConversationRole.TEAM
        else:
            role = ConversationRole.SHAREABLE_TEMPLATE

    # Now handle the new conversation based on its role.
    match role:
        case ConversationRole.COORDINATOR:
            try:
                # In the beginning, we created a share...
                share_id = await ShareManager.create_share(context)

                # And it was good. So we then created a sharable conversation that we use as a template.
                share_url = await ShareManager.create_shareable_team_conversation(context=context, share_id=share_id)

                # Pop open the inspector panel.
                await context.send_conversation_state_event(
                    AssistantStateEvent(
                        state_id="brief",
                        event="focus",
                        state=None,
                    )
                )

                # Run task-detection agents.
                audience_task = asyncio.create_task(
                    agentic.detect_audience_and_takeaways(context, attachments_extension)
                )
                gaps_task = asyncio.create_task(agentic.detect_knowledge_package_gaps(context, attachments_extension))
                audience_task.add_done_callback(lambda t: t.exception() if t.done() and t.exception() else None)
                gaps_task.add_done_callback(lambda t: t.exception() if t.done() and t.exception() else None)
                await asyncio.gather(audience_task, gaps_task, return_exceptions=True)

                # Kick off the task actor.
                metadata: dict[str, Any] = {
                    "debug": {
                        "share_id": share_id,
                    }
                }
                await agentic.act(context, attachments_extension, metadata)

                # Prepare a generic welcome message.
                config = await assistant_config.get(context.assistant)
                welcome_message = config.coordinator_config.welcome_message.format(
                    share_url=share_url or "<Share URL generation failed>"
                )
            except Exception as e:
                welcome_message = f"I'm having trouble setting up your knowledge transfer. Please try again or contact support if the issue persists. {e!s}"  # noqa: E501

            await context.send_messages(
                NewConversationMessage(
                    content=welcome_message,
                    message_type=MessageType.chat,
                )
            )

        case ConversationRole.SHAREABLE_TEMPLATE:
            # Associate the shareable template with a share ID
            if not share_id:
                logger.error("No share ID found for shareable team conversation.")
                return
            await ShareManager.set_conversation_role(context, share_id, ConversationRole.SHAREABLE_TEMPLATE)
            return

        case ConversationRole.TEAM:
            if not share_id:
                logger.error("No share ID found for team conversation.")
                return

            # I'd put status messages here, but the attachment's extension is causing race conditions.
            await context.send_messages(
                NewConversationMessage(
                    content="Hold on a second while I set up your space...",
                    message_type=MessageType.chat,
                )
            )

            await ShareManager.set_conversation_role(context, share_id, ConversationRole.TEAM)
            await ShareFilesManager.synchronize_files_to_team_conversation(context=context, share_id=share_id)

            welcome_message, debug = await agentic.generate_team_welcome_message(context)
            await context.send_messages(
                NewConversationMessage(
                    content=welcome_message,
                    message_type=MessageType.chat,
                    metadata={
                        "generated_content": True,
                        "debug": debug,
                    },
                )
            )

            # Pop open the inspector panel.
            await context.send_conversation_state_event(
                AssistantStateEvent(
                    state_id="brief",
                    event="focus",
                    state=None,
                )
            )

            return


@assistant.events.conversation.on_updated
async def on_conversation_updated(context: ConversationContext) -> None:
    """
    Handle conversation updates (including title changes) and sync with shareable template.
    """
    try:
        conversation = await context.get_conversation()
        role = await ShareManager.get_conversation_role(context)
        if role != ConversationRole.COORDINATOR:
            return

        shared_conversation_id = await ShareManager.get_shared_conversation_id(context)
        if not shared_conversation_id:
            return

        # Update the shareable template conversation's title if needed.
        try:
            target_context = context.for_conversation(shared_conversation_id)
            target_conversation = await target_context.get_conversation()
            if target_conversation.title != conversation.title:
                await target_context.update_conversation_title(conversation.title)
                logger.debug(
                    f"Updated conversation {shared_conversation_id} title from '{target_conversation.title}' to '{conversation.title}'"  # noqa: E501
                )
            else:
                logger.debug(f"Conversation {shared_conversation_id} title already matches: '{conversation.title}'")
        except Exception as title_update_error:
            logger.error(f"Error updating conversation {shared_conversation_id} title: {title_update_error}")

    except Exception as e:
        logger.error(f"Error syncing conversation title: {e}")


async def store_coordinator_message(context: ConversationContext, message: ConversationMessage) -> None:
    async with context.set_status("jotting..."):
        try:
            sender_name = "Coordinator"
            if message.sender:
                participants = await context.get_participants()
                for participant in participants.participants:
                    if participant.id == message.sender.participant_id:
                        sender_name = participant.name
                        break

                await ShareManager.append_coordinator_message(
                    context=context,
                    message_id=str(message.id),
                    content=message.content,
                    sender_name=sender_name,
                    is_assistant=message.sender.participant_role == ParticipantRole.assistant,
                    timestamp=message.timestamp,
                )
        except Exception as e:
            logger.exception(f"Error storing Coordinator message for Team access: {e}")


@assistant.events.conversation.message.chat.on_created
async def on_message_created(
    context: ConversationContext, event: ConversationEvent, message: ConversationMessage
) -> None:
    await context.update_participant_me(UpdateParticipant(status="thinking..."))

    metadata: dict[str, Any] = {
        "debug": {
            "content_safety": event.data.get(content_safety.metadata_key, {}),
        }
    }

    try:
        share = await ShareManager.get_share(context)
        metadata["debug"]["share_id"] = share.share_id
        is_user_message = message.sender.participant_role == ParticipantRole.user
        user_information_requests: list[str] | None = None

        # Save coordinator-role user messages for team access.
        role = await ShareManager.get_conversation_role(context)
        if role == ConversationRole.COORDINATOR and is_user_message:
            await store_coordinator_message(context, message)

        if message.message_type == MessageType.chat and is_user_message:
            async with context.set_status("pondering..."):
                if role == ConversationRole.COORDINATOR:
                    # Update knowledge digest.
                    digest_task = asyncio.create_task(agentic.update_digest(context, attachments_extension))
                    digest_task.add_done_callback(lambda t: t.exception() if t.done() and t.exception() else None)

                    parallel_tasks = []

                    # Solicit audience and audience takeaway tasks.
                    audience_task = asyncio.create_task(
                        agentic.detect_audience_and_takeaways(context, attachments_extension)
                    )
                    audience_task.add_done_callback(lambda t: t.exception() if t.done() and t.exception() else None)
                    parallel_tasks.append(audience_task)

                    # Solicit knowledge package gap tasks.
                    gaps_task = asyncio.create_task(
                        agentic.detect_knowledge_package_gaps(context, attachments_extension)
                    )
                    gaps_task.add_done_callback(lambda t: t.exception() if t.done() and t.exception() else None)
                    parallel_tasks.append(gaps_task)

                    # Detect coordinator actions
                    # coordinator_actions_task = asyncio.create_task(
                    #     agentic.detect_coordinator_actions(context, attachments_extension)
                    # )
                    # coordinator_actions_task.add_done_callback(
                    #     lambda t: t.exception() if t.done() and t.exception() else None
                    # )

                    # Run all of the tasks in parallel and wait for their return.
                    await asyncio.gather(*parallel_tasks, return_exceptions=True)

                    # task5 = asyncio.create_task(agentic.focus(context, attachments_extension))
                    # task5.add_done_callback(lambda t: t.exception() if t.done() and t.exception() else None)

                    # Now, let's act on all the tasks.
                    await agentic.act(context, attachments_extension, metadata)

                if role == ConversationRole.TEAM:
                    # For team role, analyze message for possible information request needs.
                    # Send a notification if we think it might be one.
                    detection_result = await agentic.detect_information_request_needs(context, message.content)

                    if (
                        detection_result.get("is_information_request", False)
                        and detection_result.get("confidence", 0) > 0.8
                    ):
                        suggested_title = detection_result.get("potential_title", "")
                        suggested_priority = detection_result.get("suggested_priority", "medium")
                        potential_description = detection_result.get("potential_description", "")
                        reason = detection_result.get("reason", "")

                        # TODO: replace this with the sub-agent creating tasks.
                        await context.send_messages(
                            NewConversationMessage(
                                content=(
                                    f"**Potential _Information Request_ Detected**\n\n"
                                    f"You might need information from the knowledge coordinator. {reason}\n\n"
                                    f"Would you like me to create an information request?\n"
                                    f"**Title:** {suggested_title}\n"
                                    f"**Description:** {potential_description}\n"
                                    f"**Priority:** {suggested_priority}\n\n"
                                ),
                                message_type=MessageType.notice,
                                metadata={"debug": detection_result},
                            )
                        )

                # Generate message.
                response = await respond_to_conversation(
                    context,
                    new_message=message,
                    attachments_extension=attachments_extension,
                    metadata=metadata,
                    user_information_requests=user_information_requests,
                )
                content = ""
                if response:
                    content = str(response.get("content", ""))

                # strip out the username from the response
                if content.startswith("["):
                    content = re.sub(r"\[.*\]:\s", "", content)

                # If there are more than one user participants in the conversation, we need
                # to check if the model chose to remain silent.
                if content and content.replace(" ", "") == SILENCE_TOKEN:
                    config = await assistant_config.get(context.assistant)
                    if config.enable_debug_output:
                        metadata["debug"]["silence_token"] = True
                        metadata["debug"]["silence_token_response"] = (content,)
                        await context.send_messages(
                            NewConversationMessage(
                                message_type=MessageType.notice,
                                content="[assistant chose to remain silent]",
                                metadata=metadata,
                            )
                        )
                    return

                # Prepare response.
                response_parts: list[str] = []
                if not content:
                    return
                try:
                    if role == ConversationRole.TEAM:
                        output_model = TeamOutput.model_validate_json(content)
                        if output_model.response:
                            response_parts.append(output_model.response)

                        if output_model.excerpt:
                            output_model.excerpt = output_model.excerpt.strip().strip('"')
                            response_parts.append(f'> _"{output_model.excerpt}"_ (excerpt)')

                        if output_model.citations:
                            citations = ", ".join(output_model.citations)
                            response_parts.append(f"Sources: _{citations}_")

                        if output_model.next_step_suggestion:
                            metadata["help"] = output_model.next_step_suggestion

                    if role == ConversationRole.COORDINATOR:
                        output_model = CoordinatorOutput.model_validate_json(content)
                        if output_model.response:
                            response_parts.append(output_model.response)
                        # if output_model.next_step_suggestion:
                        #     metadata["help"] = output_model.next_step_suggestion

                    await context.send_messages(
                        NewConversationMessage(
                            content="\n\n".join(response_parts),
                            message_type=MessageType.chat,
                            metadata=metadata,
                        )
                    )

                    # Save valid assistant responses for team access.
                    await store_coordinator_message(
                        context,
                        ConversationMessage(
                            id=message.id,
                            content_type=message.content_type,
                            content="\n\n".join(response_parts),
                            sender=message.sender,
                            timestamp=message.timestamp,
                            message_type=MessageType.chat,
                            filenames=[],
                            metadata={},
                            has_debug_data=False,
                        ),
                    )

                except Exception as e:
                    metadata["debug"]["error"] = str(e)
                    logger.exception(f"exception occurred parsing json response: {e}")
                    NewConversationMessage(
                        content="I'm sorry, I encountered an error while processing the response.",
                        message_type=MessageType.notice,
                        metadata=metadata,
                    )

    except Exception as e:
        logger.exception(f"Error handling message: {e}")
        await context.send_messages(
            NewConversationMessage(
                content=f"Error: {e!s}",
                message_type=MessageType.notice,
                metadata={"generated_content": False, **metadata},
            )
        )
    finally:
        await context.update_participant_me(UpdateParticipant(status=None))


@assistant.events.conversation.message.command.on_created
async def on_command_created(
    context: ConversationContext, event: ConversationEvent, message: ConversationMessage
) -> None:
    if message.message_type != MessageType.command:
        return

    await context.update_participant_me(UpdateParticipant(status="processing command..."))
    try:
        metadata = {"debug": {"content_safety": event.data.get(content_safety.metadata_key, {})}}

        # Respond to the conversation
        await respond_to_conversation(
            context,
            new_message=message,
            attachments_extension=attachments_extension,
            metadata=metadata,
        )
    finally:
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
    1. Store a copy in share storage
    2. Synchronize to all Team conversations

    For Team files:
    1. Use as-is without copying to share storage
    """
    try:
        if not file.filename:
            logger.warning(f"No share found or missing filename. filename={file.filename}")
            return

        share = await ShareManager.get_share(context)
        role = await ShareManager.get_conversation_role(context)

        # Process based on role
        if role == ConversationRole.COORDINATOR:
            # For Coordinator files:
            # 1. Store in share storage (marked as coordinator file)

            success = await ShareFilesManager.copy_file_to_share_storage(
                context=context,
                share_id=share.share_id,
                file=file,
                is_coordinator_file=True,
            )

            if not success:
                logger.error(f"Failed to copy file to share storage: {file.filename}")
                return

            # 2. Synchronize to all Team conversations
            # Get all Team conversations
            team_conversations = await ShareFilesManager.get_team_conversations(context, share.share_id)

            if team_conversations:
                for team_conv_id in team_conversations:
                    await ShareFilesManager.copy_file_to_conversation(
                        context=context,
                        share_id=share.share_id,
                        filename=file.filename,
                        target_conversation_id=team_conv_id,
                    )

            # 3. Update all UIs but don't send notifications to reduce noise
            await Notifications.notify_all_state_update(context, [InspectorTab.DEBUG])
        # Team files don't need special handling as they're already in the conversation

        # Log file creation to knowledge transfer log for all files
        await ShareManager.log_share_event(
            context=context,
            entry_type="file_shared",
            message=f"File shared: {file.filename}",
            metadata={
                "file_id": getattr(file, "id", ""),
                "filename": file.filename,
                "is_coordinator_file": role == ConversationRole.COORDINATOR,
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
    try:
        if not file.filename:
            return

        share = await ShareManager.get_share(context)
        role = await ShareManager.get_conversation_role(context)
        if role == ConversationRole.COORDINATOR:
            # For Coordinator files:
            # 1. Update in share storage
            success = await ShareFilesManager.copy_file_to_share_storage(
                context=context,
                share_id=share.share_id,
                file=file,
                is_coordinator_file=True,
            )

            if not success:
                logger.error(f"Failed to update file in share storage: {file.filename}")
                return

            team_conversations = await ShareFilesManager.get_team_conversations(context, share.share_id)
            for team_conv_id in team_conversations:
                await ShareFilesManager.copy_file_to_conversation(
                    context=context,
                    share_id=share.share_id,
                    filename=file.filename,
                    target_conversation_id=team_conv_id,
                )

            # 3. Update all UIs but don't send notifications to reduce noise
            await Notifications.notify_all_state_update(context, [InspectorTab.DEBUG])

        await ShareManager.log_share_event(
            context=context,
            entry_type="file_shared",
            message=f"File updated: {file.filename}",
            metadata={
                "file_id": getattr(file, "id", ""),
                "filename": file.filename,
                "is_coordinator_file": role == ConversationRole.COORDINATOR,
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
    try:
        if not file.filename:
            return

        share = await ShareManager.get_share(context)
        role = await ShareManager.get_conversation_role(context)
        if role == ConversationRole.COORDINATOR:
            # For Coordinator files:
            # 1. Delete from share storage
            success = await ShareFilesManager.delete_file_from_knowledge_share_storage(
                context=context, share_id=share.share_id, filename=file.filename
            )

            if not success:
                logger.error(f"Failed to delete file from share storage: {file.filename}")

            # 2. Update all UIs about the deletion but don't send notifications to reduce noise
            await Notifications.notify_all_state_update(context, [InspectorTab.DEBUG])
        # Team files don't need special handling

        await ShareManager.log_share_event(
            context=context,
            entry_type="file_deleted",
            message=f"File deleted: {file.filename}",
            metadata={
                "file_id": getattr(file, "id", ""),
                "filename": file.filename,
                "is_coordinator_file": role == ConversationRole.COORDINATOR,
            },
        )

    except Exception as e:
        logger.exception(f"Error handling file deletion: {e}")


@assistant.events.conversation.participant.on_created
async def on_participant_joined(
    context: ConversationContext,
    event: ConversationEvent,
    participant: workbench_model.ConversationParticipant,
) -> None:
    try:
        if participant.id == context.assistant.id:
            return

        # Open the Brief tab (state inspector).
        await context.send_conversation_state_event(
            AssistantStateEvent(
                state_id="brief",
                event="focus",
                state=None,
            )
        )

        role = await ShareManager.get_conversation_role(context)
        if role != ConversationRole.TEAM:
            return

        share_id = await ShareManager.get_share_id(context)
        if not share_id:
            return

        await ShareFilesManager.synchronize_files_to_team_conversation(context=context, share_id=share_id)

        await ShareManager.log_share_event(
            context=context,
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
