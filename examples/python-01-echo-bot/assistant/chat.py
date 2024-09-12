# Copyright (c) Microsoft. All rights reserved.

# An example for building a simple message echo assistant using the AssistantApp from
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
from typing import Any

from semantic_workbench_api_model.workbench_model import (
    ConversationEvent,
    ConversationMessage,
    MessageType,
    NewConversationMessage,
    UpdateParticipant,
)
from semantic_workbench_assistant.assistant_app import (
    AssistantApp,
    BaseModelAssistantConfig,
    ConversationContext,
)

from .config import AssistantConfigModel, ui_schema

logger = logging.getLogger(__name__)

#
# define the service ID, name, and description
#

# the service id to be registered in the workbench to identify the assistant
service_id = "python-01-echo-bot.workbench-explorer"
# the name of the assistant service, as it will appear in the workbench UI
service_name = "Python Example 01: Echo Bot"
# a description of the assistant service, as it will appear in the workbench UI
service_description = "A starter for building a chat assistant using the Semantic Workbench Assistant SDK."

#
# create the configuration provider, using the extended configuration model
#
config_provider = BaseModelAssistantConfig(AssistantConfigModel(), ui_schema=ui_schema)

# create the AssistantApp instance
assistant = AssistantApp(
    assistant_service_id=service_id,
    assistant_service_name=service_name,
    assistant_service_description=service_description,
    config_provider=config_provider,
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
    # ignore messages from this assistant
    if message.sender.participant_id == context.assistant.id:
        return

    # update the participant status to indicate the assistant is thinking
    await context.update_participant_me(UpdateParticipant(status="thinking..."))
    try:
        # replace the following with your own logic for processing a message created event
        await respond_to_conversation(
            context,
            message=message,
            metadata={"debug": {"content_safety": event.data.get(assistant.content_interceptor.metadata_key, {})}},
        )
    finally:
        # update the participant status to indicate the assistant is done thinking
        await context.update_participant_me(UpdateParticipant(status=None))


# Handle the event triggered when the assistant is added to a conversation.
@assistant.events.conversation.on_created
async def on_conversation_created(context: ConversationContext) -> None:
    """
    Handle the event triggered when the assistant is added to a conversation.
    """
    # replace the following with your own logic for processing a conversation created event

    # get the assistant's configuration
    assistant_config = await config_provider.get_typed(context.assistant)

    # get the welcome message from the assistant's configuration
    welcome_message = assistant_config.welcome_message

    # send the welcome message to the conversation
    await context.send_messages(
        NewConversationMessage(
            content=welcome_message,
            message_type=MessageType.chat,
            metadata={"generated_content": False},
        )
    )


# endregion


# region Custom
#
# This code was added specifically for this example to demonstrate how to respond to conversation
# messages simply echoing back the input message. For your own assistant, you could replace this
# code with your own logic for responding to conversation messages and add any additional
# functionality as needed.
#


# demonstrates how to respond to a conversation message echoing back the input message
async def respond_to_conversation(
    context: ConversationContext, message: ConversationMessage, metadata: dict[str, Any] = {}
) -> None:
    """
    Respond to a conversation message.
    """

    # get the assistant's configuration
    assistant_config = await config_provider.get_typed(context.assistant)

    # send a new message with the echo response
    await context.send_messages(
        NewConversationMessage(
            content=f"echo: {message.content}",
            message_type=MessageType.chat,
            # add debug metadata if debug output is enabled
            # any content in the debug property on the metadata
            # will be displayed in the workbench UI for inspection
            metadata=(
                {
                    "debug": {
                        "source": "echo",
                        "original_message": message,
                        **metadata,
                    }
                }
                if assistant_config.enable_debug_output
                else metadata
            ),
        )
    )


# endregion
