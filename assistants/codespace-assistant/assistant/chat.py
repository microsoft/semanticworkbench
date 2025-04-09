# Copyright (c) Microsoft. All rights reserved.

# Prospector Assistant
#
# This assistant helps you mine ideas from artifacts.
#

import logging
from typing import Any

import deepmerge
from assistant_extensions.attachments import AttachmentsExtension
from assistant_extensions.document_editor import DocumentEditorConfigModel, DocumentEditorExtension
from content_safety.evaluators import CombinedContentSafetyEvaluator
from semantic_workbench_api_model.workbench_model import (
    ConversationEvent,
    ConversationMessage,
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import (
    AssistantApp,
    AssistantContext,
    AssistantTemplate,
    BaseModelAssistantConfig,
    ContentSafety,
    ContentSafetyEvaluator,
    ConversationContext,
)

from .config import AssistantConfigModel, ContextTransferConfigModel, DocumentAssistantConfigModel, MCPToolsConfigModel
from .response import respond_to_conversation

logger = logging.getLogger(__name__)

#
# region Setup
#

# the service id to be registered in the workbench to identify the assistant
service_id = "codespace-assistant.made-exploration-team"
# the name of the assistant service, as it will appear in the workbench UI
service_name = "Codespace Assistant"
# a description of the assistant service, as it will appear in the workbench UI
service_description = "An assistant for developing in the Codespaces."

#
# create the configuration provider, using the extended configuration model
#
assistant_config = BaseModelAssistantConfig(
    AssistantConfigModel,
    additional_templates={
        "workspace": DocumentAssistantConfigModel,
        "context_transfer": ContextTransferConfigModel,
    },
)


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
    additional_templates=[
        AssistantTemplate(
            id="workspace",
            name="Document Assistant",
            description="An assistant for creating and editing documents.",
        ),
        AssistantTemplate(
            id="context_transfer",
            name="Context Transfer Assistant",
            description="An assistant for transferring context.",
        ),
    ],
)


async def tools_config_provider(context: AssistantContext) -> MCPToolsConfigModel:
    return (await assistant_config.get(context)).tools


async def document_editor_config_provider(ctx: ConversationContext) -> DocumentEditorConfigModel:
    config = await assistant_config.get(ctx.assistant)
    return config.extensions_config.document_editor


document_editor_extension = DocumentEditorExtension(
    app=assistant,
    config_provider=document_editor_config_provider,
    storage_directory="documents",
)


attachments_extension = AttachmentsExtension(assistant)

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
        document_editor_extension.lock_document_edits(context),
    ):
        config = await assistant_config.get(context.assistant)
        metadata: dict[str, Any] = {"debug": {"content_safety": event.data.get(content_safety.metadata_key, {})}}

        try:
            await respond_to_conversation(
                message=message,
                attachments_extension=attachments_extension,
                document_editor_extension=document_editor_extension,
                context=context,
                config=config,
                metadata=metadata,
            )
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
    if config.response_behavior.only_respond_to_mentions and f"@{context.assistant.name}" not in message.content:
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
    welcome_message = config.response_behavior.welcome_message
    await context.send_messages(
        NewConversationMessage(
            content=welcome_message,
            message_type=MessageType.chat,
            metadata={"generated_content": False},
        )
    )


# endregion
