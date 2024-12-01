# Copyright (c) Microsoft. All rights reserved.

# Prospector Assistant
#
# This assistant helps you mine ideas from artifacts.
#

import logging
from typing import Any

import deepmerge
from assistant_extensions.artifacts import ArtifactsExtension
from assistant_extensions.artifacts._model import ArtifactsConfigModel
from assistant_extensions.attachments import AttachmentsExtension
from assistant_extensions.workflows import WorkflowsConfigModel, WorkflowsExtension
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
    BaseModelAssistantConfig,
    ContentSafety,
    ContentSafetyEvaluator,
    ConversationContext,
)

from .config import AssistantConfigModel
from .response import respond_to_conversation

logger = logging.getLogger(__name__)

#
# region Setup
#

# the service id to be registered in the workbench to identify the assistant
service_id = "explorer-assistant.made-exploration-team"
# the name of the assistant service, as it will appear in the workbench UI
service_name = "Explorer Assistant"
# a description of the assistant service, as it will appear in the workbench UI
service_description = "An assistant for exploring capabilities."

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


async def artifacts_config_provider(context: AssistantContext) -> ArtifactsConfigModel:
    return (await assistant_config.get(context)).extensions_config.artifacts


async def workflows_config_provider(context: AssistantContext) -> WorkflowsConfigModel:
    return (await assistant_config.get(context)).extensions_config.workflows


artifacts_extension = ArtifactsExtension(assistant, artifacts_config_provider)
attachments_extension = AttachmentsExtension(assistant)
workflows_extension = WorkflowsExtension(assistant, "content_safety", workflows_config_provider)

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

    # ignore messages that are directed at a participant other than this assistant
    if message.metadata.get("directed_at") and message.metadata["directed_at"] != context.assistant.id:
        return

    # ignore messages that @mention a participant other than this assistant
    if message.metadata.get("mentions") and context.assistant.id not in message.metadata["mentions"]:
        return

    # update the participant status to indicate the assistant is thinking
    async with context.set_status("thinking..."):
        config = await assistant_config.get(context.assistant)
        metadata: dict[str, Any] = {"debug": {"content_safety": event.data.get(content_safety.metadata_key, {})}}

        try:
            # Prospector assistant response
            await respond_to_conversation(
                artifacts_extension=artifacts_extension,
                attachments_extension=attachments_extension,
                context=context,
                config=config,
                metadata=metadata,
            )
        except Exception as e:
            logger.exception(f"exception occurred responding to conversation: {e}")
            deepmerge.always_merger.merge(metadata, {"debug": {"error": str(e)}})
            await context.send_messages(
                NewConversationMessage(
                    content="An error occurred while responding to the conversation. View the debug inspector for more information.",
                    message_type=MessageType.notice,
                    metadata=metadata,
                )
            )


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
    welcome_message = config.welcome_message
    await context.send_messages(
        NewConversationMessage(
            content=welcome_message,
            message_type=MessageType.chat,
            metadata={"generated_content": False},
        )
    )


# endregion
