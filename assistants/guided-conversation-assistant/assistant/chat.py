# Copyright (c) Microsoft. All rights reserved.

# Prospector Assistant
#
# This assistant helps you mine ideas from artifacts.
#

import logging
from typing import Any

import deepmerge
import openai_client
from content_safety.evaluators import CombinedContentSafetyEvaluator
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

from .agents.guided_conversation_agent import (
    GuidedConversationAgent,
    GuidedConversationConversationInspectorStateProvider,
)
from .config import AssistantConfigModel

logger = logging.getLogger(__name__)

#
# region Setup
#

# the service id to be registered in the workbench to identify the assistant
service_id = "guided-conversation-assistant.made-exploration"
# the name of the assistant service, as it will appear in the workbench UI
service_name = "Guided Conversation Assistant"
# a description of the assistant service, as it will appear in the workbench UI
service_description = "An assistant that will guide users through a conversation towards a specific goal."

#
# create the configuration provider, using the extended configuration model
#
assistant_config = BaseModelAssistantConfig(AssistantConfigModel)


# define the content safety evaluator factory
async def content_evaluator_factory(context: ConversationContext) -> ContentSafetyEvaluator:
    config = await assistant_config.get(context.assistant)
    return CombinedContentSafetyEvaluator(config.content_safety_config)


content_safety = ContentSafety(content_evaluator_factory)

guided_conversation_conversation_inspector_state_provider = GuidedConversationConversationInspectorStateProvider(
    assistant_config
)

# create the AssistantApp instance
assistant = AssistantApp(
    assistant_service_id=service_id,
    assistant_service_name=service_name,
    assistant_service_description=service_description,
    config_provider=assistant_config.provider,
    content_interceptor=content_safety,
    inspector_state_providers={
        "guided_conversation": guided_conversation_conversation_inspector_state_provider,
    },
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

    # ignore messages from this assistant
    if message.sender.participant_id == context.assistant.id:
        return

    # update the participant status to indicate the assistant is thinking
    await context.update_participant_me(UpdateParticipant(status="thinking..."))
    try:
        # respond to the conversation message
        await respond_to_conversation(
            context,
            metadata={"debug": {"content_safety": event.data.get(content_safety.metadata_key, {})}},
        )

    finally:
        # update the participant status to indicate the assistant is done thinking
        await context.update_participant_me(UpdateParticipant(status=None))


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
    # don't wait for the response
    _ = respond_to_conversation(context)


# endregion


#
# region Response
#


# demonstrates how to respond to a conversation message using the guided conversation library
async def respond_to_conversation(context: ConversationContext, metadata: dict[str, Any] = {}) -> None:
    """
    Respond to a conversation message.

    This method uses the guided conversation agent to respond to a conversation message. The guided conversation
    agent is designed to guide the conversation towards a specific goal as specified in its definition.
    """

    # define the metadata key for any metadata created within this method
    method_metadata_key = "respond_to_conversation"

    # get the assistant's configuration, supports overwriting defaults from environment variables
    config = await assistant_config.get(context.assistant)

    # initialize variables for the response content
    content: str | None = None

    guided_conversation = GuidedConversationAgent()
    try:
        content = await guided_conversation.step_conversation(
            conversation_context=context,
            openai_client=openai_client.create_client(config.service_config),
            request_config=config.request_config,
            agent_config=config.agents_config.guided_conversation_agent,
        )
        # add the completion to the metadata for debugging
        deepmerge.always_merger.merge(
            metadata,
            {
                "debug": {
                    f"{method_metadata_key}": {"response": content},
                }
            },
        )
    except Exception as e:
        logger.exception(f"exception occurred processing guided conversation: {e}")
        content = "An error occurred while processing the guided conversation."
        deepmerge.always_merger.merge(
            metadata,
            {
                "debug": {
                    f"{method_metadata_key}": {
                        "error": str(e),
                    },
                }
            },
        )

    # add the state to the metadata for debugging
    state = guided_conversation.get_state(context)
    deepmerge.always_merger.merge(
        metadata,
        {
            "debug": {
                f"{method_metadata_key}": {
                    "state": state,
                },
            }
        },
    )

    # send the response to the conversation
    await context.send_messages(
        NewConversationMessage(
            content=content or "[no response from assistant]",
            message_type=MessageType.chat if content else MessageType.note,
            metadata=metadata,
        )
    )

    await context.send_conversation_state_event(
        AssistantStateEvent(
            state_id="guided_conversation",
            event="updated",
            state=None,
        )
    )


# endregion
