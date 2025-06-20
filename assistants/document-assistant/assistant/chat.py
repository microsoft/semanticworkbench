# Copyright (c) Microsoft. All rights reserved.

#
# Document Assistant
#

import asyncio
import logging
import pathlib
from textwrap import dedent
from typing import Any

import deepmerge
from assistant_extensions import dashboard_card, navigator
from assistant_extensions.mcp import MCPServerConfig
from content_safety.evaluators import CombinedContentSafetyEvaluator
from semantic_workbench_api_model.workbench_model import (
    ConversationEvent,
    ConversationMessage,
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import (
    AssistantApp,
    BaseModelAssistantConfig,
    ContentSafety,
    ContentSafetyEvaluator,
    ConversationContext,
)

from assistant.config import AssistantConfigModel
from assistant.context_management.conv_compaction import task_compact_conversation
from assistant.context_management.file_manager import task_score_files
from assistant.context_management.inspector import ContextManagementInspector
from assistant.filesystem import AttachmentsExtension, DocumentEditorConfigModel
from assistant.guidance.dynamic_ui_inspector import DynamicUIInspector
from assistant.response.responder import ConversationResponder
from assistant.whiteboard import WhiteboardInspector

logger = logging.getLogger(__name__)

# region Setup

# the service id to be registered in the workbench to identify the assistant
service_id = "document-assistant.made-exploration-team"
# the name of the assistant service, as it will appear in the workbench UI
service_name = "Document Assistant"
# a description of the assistant service, as it will appear in the workbench UI
service_description = "An assistant for writing documents."

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
    assistant_service_metadata={
        **dashboard_card.metadata(
            dashboard_card.TemplateConfig(
                enabled=True,
                template_id="default",
                icon=dashboard_card.image_to_url(
                    pathlib.Path(__file__).parent / "assets" / "icon.svg", "image/svg+xml"
                ),
                background_color="rgb(155,217,219)",
                card_content=dashboard_card.CardContent(
                    content_type="text/markdown",
                    content=dedent(
                        """
                        General assistant focused on document creation and editing.\n
                        - Side by side doc editing
                        - Provides guidance through generated UI elements
                        - Autonomously executes tools to complete tasks.
                        - Local-only options for Office integration via MCP"""
                    ),
                ),
            )
        ),
        **navigator.metadata_for_assistant_navigator({
            "default": (pathlib.Path(__file__).parent / "text_includes" / "document_assistant_info.md").read_text(
                "utf-8"
            ),
        }),
    },
)


async def document_editor_config_provider(ctx: ConversationContext) -> DocumentEditorConfigModel:
    config = await assistant_config.get(ctx.assistant)
    # Get either the hosted or personal config based on which one is enabled. Priority is given to the personal config.
    personal_filesystem_edit = [x for x in config.orchestration.personal_mcp_servers if x.key == "filesystem-edit"]
    if len(personal_filesystem_edit) > 0:
        return personal_filesystem_edit[0]
    return config.orchestration.hosted_mcp_servers.filesystem_edit


async def whiteboard_config_provider(ctx: ConversationContext) -> MCPServerConfig:
    config = await assistant_config.get(ctx.assistant)
    return config.orchestration.hosted_mcp_servers.memory_whiteboard


_ = WhiteboardInspector(state_id="whiteboard", app=assistant, server_config_provider=whiteboard_config_provider)
_ = DynamicUIInspector(state_id="dynamic_ui", app=assistant)


async def context_management_config_provider(ctx: ConversationContext) -> AssistantConfigModel:
    """
    Provide the configuration for the context management inspector.
    This is used to determine if the inspector should be enabled or not.
    """
    config = await assistant_config.get(ctx.assistant)
    return config


attachments_extension = AttachmentsExtension(assistant, config_provider=document_editor_config_provider)

context_management_inspector = ContextManagementInspector(
    app=assistant, config_provider=context_management_config_provider
)

#
# create the FastAPI app instance
#
app = assistant.fastapi_app()


# endregion


#
# region Event Handlers
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

    # check if the assistant should respond to the message
    if not await should_respond_to_message(context, message):
        return

    # update the participant status to indicate the assistant is thinking
    async with (
        context.set_status("thinking..."),
        attachments_extension.lock_document_edits(context),
    ):
        config = await assistant_config.get(context.assistant)
        metadata: dict[str, Any] = {"debug": {"content_safety": event.data.get(content_safety.metadata_key, {})}}

        asyncio.create_task(  # Fire off the compaction task in the background
            task_compact_conversation(context=context, config=config, attachments_extension=attachments_extension)
        )

        try:
            responder = await ConversationResponder.create(
                message=message,
                context=context,
                config=config,
                metadata=metadata,
                attachments_extension=attachments_extension,
                context_management_inspector=context_management_inspector,
            )
            await responder.respond_to_conversation()
        except Exception as e:
            logger.exception(f"Exception occurred responding to conversation: {e}")
            deepmerge.always_merger.merge(metadata, {"debug": {"error": str(e)}})
            await context.send_messages(
                NewConversationMessage(
                    content="An error occurred while responding to the conversation. View the debug inspector for more information.",
                    message_type=MessageType.notice,
                    metadata=metadata,
                )
            )

        asyncio.create_task(
            task_score_files(
                context=context,
                config=config,
                attachments_extension=attachments_extension,
                context_management_inspector=context_management_inspector,
            )
        )


async def should_respond_to_message(context: ConversationContext, message: ConversationMessage) -> bool:
    """
    Determine if the assistant should respond to the message.

    This method can be used to implement custom logic to determine if the assistant should respond to a message.
    By default, the assistant will respond to all messages.

    Args:
        context: The conversation context.
        message: The message to evaluate.

    Returns:
        bool: True if the assistant should respond to the message; otherwise, False.
    """
    config = await assistant_config.get(context.assistant)

    # ignore messages that are directed at a participant other than this assistant
    if message.metadata.get("directed_at") and message.metadata["directed_at"] != context.assistant.id:
        return False

    # if configure to only respond to mentions, ignore messages where the content does not mention the assistant somewhere in the message
    if config.orchestration.options.only_respond_to_mentions and f"@{context.assistant.name}" not in message.content:
        # check to see if there are any other assistants in the conversation
        participant_list = await context.get_participants()
        other_assistants = [
            participant
            for participant in participant_list.participants
            if participant.role == "assistant" and participant.id != context.assistant.id
        ]
        if len(other_assistants) == 0:
            # no other assistants in the conversation, check the last 10 notices to see if the assistant has warned the user
            assistant_messages = await context.get_messages(
                participant_ids=[context.assistant.id], message_types=[MessageType.notice], limit=10
            )
            at_mention_warning_key = "at_mention_warning"
            if len(assistant_messages.messages) == 0 or all(
                at_mention_warning_key not in message.metadata for message in assistant_messages.messages
            ):
                # assistant has not been mentioned in the last 10 messages, send a warning message in case the user is not aware
                # that the assistant needs to be mentioned to receive a response
                await context.send_messages(
                    NewConversationMessage(
                        content=f"{context.assistant.name} is configured to only respond to messages that @mention it. Please @mention the assistant in your message to receive a response.",
                        message_type=MessageType.notice,
                        metadata={at_mention_warning_key: True},
                    )
                )

        return False

    return True


@assistant.events.conversation.on_created
async def on_conversation_created(context: ConversationContext) -> None:
    """
    Handle the event triggered when the assistant is added to a conversation.
    """

    assistant_sent_messages = await context.get_messages(participant_ids=[context.assistant.id], limit=1)
    welcome_sent_before = len(assistant_sent_messages.messages) > 0
    if welcome_sent_before:
        return

    # send a welcome message to the conversation
    config = await assistant_config.get(context.assistant)
    welcome_message = config.orchestration.prompts.welcome_message
    await context.send_messages(
        NewConversationMessage(
            content=welcome_message,
            message_type=MessageType.chat,
            metadata={"generated_content": False},
        )
    )


# endregion
