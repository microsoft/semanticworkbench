# Copyright (c) Microsoft. All rights reserved.

# An example for building a multi model chat assistant using the AssistantApp from
# the semantic-workbench-assistant package.
#
# This example demonstrates how to use the AssistantApp to create a chat assistant,
# to add additional configuration fields and UI schema for the configuration fields,
# and to handle conversation events to respond to messages in the conversation.
# It supports multiple AI models, including OpenAI, Azure, Anthropic, and Gemini.
# It provides a general message handler to respond to chat messages using the selected AI model.

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

import tiktoken
from semantic_workbench_api_model.workbench_model import (
    ConversationEvent, ConversationMessage, MessageType,
    NewConversationMessage, UpdateParticipant)
from semantic_workbench_assistant.assistant_app import (
    AssistantApp, BaseModelAssistantConfig, ContentSafety,
    ContentSafetyEvaluator, ConversationContext)

from .config import AssistantConfigModel, ui_schema
from .model_adapters import Message, get_model_adapter
from .responsible_ai.azure_evaluator import AzureContentSafetyEvaluator
from .responsible_ai.openai_evaluator import (
    OpenAIContentSafetyEvaluator, OpenAIContentSafetyEvaluatorConfigModel)

logger = logging.getLogger(__name__)

#
# define the service ID, name, and description
#

# the service id to be registered in the workbench to identify the assistant
service_id = "python-03-multimodel-chatbot.workbench-explorer"
# the name of the assistant service, as it will appear in the workbench UI
service_name = "Python Example 03: Multi model Chatbot"
# a description of the assistant service, as it will appear in the workbench UI
service_description = "A chat assistant supporting multiple AI models using the Semantic Workbench Assistant SDK."

#
# create the configuration provider, using the extended configuration model
#
config_provider = BaseModelAssistantConfig(AssistantConfigModel(), ui_schema=ui_schema)


# define the content safety evaluator factory
async def content_evaluator_factory(context: ConversationContext) -> ContentSafetyEvaluator:
    config = await config_provider.get_typed(context.assistant)

    # return the content safety evaluator based on the service type
    match config.service_config.service_type:
        case "Azure OpenAI":
            return AzureContentSafetyEvaluator(config.service_config.azure_content_safety_config)
        case "OpenAI":
            return OpenAIContentSafetyEvaluator(
                OpenAIContentSafetyEvaluatorConfigModel(openai_api_key=config.service_config.openai_api_key)
            )
        case "Anthropic":
            return AzureContentSafetyEvaluator(config.service_config.azure_content_safety_config)
        case "Gemini":
            return AzureContentSafetyEvaluator(config.service_config.azure_content_safety_config)


# create the AssistantApp instance
assistant = AssistantApp(
    assistant_service_id=service_id,
    assistant_service_name=service_name,
    assistant_service_description=service_description,
    config_provider=config_provider,
    content_interceptor=ContentSafety(content_evaluator_factory),
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
# using a message adapter to format messages for the specific AI model in use. For your own assistant,
# you could replace this code with your own logic for responding to conversation messages and add any
# additional functionality as needed.

# demonstrates how to respond to a conversation message using the model adapter.
async def respond_to_conversation(
    context: ConversationContext, message: ConversationMessage, metadata: dict[str, Any] = {}
) -> None:
    """
    Respond to a conversation message.
    """

    # define the metadata key for any metadata created within this method
    method_metadata_key = "respond_to_conversation"

    # update the participant status to indicate the assistant is thinking
    await context.update_participant_me(UpdateParticipant(status="thinking..."))

    try:
        # get the assistant's configuration
        assistant_config = await config_provider.get_typed(context.assistant)

        # get the list of conversation participants
        participants_response = await context.get_participants(include_inactive=True)

        # establish a token to be used by the AI model to indicate no response
        silence_token = "{{SILENCE}}"

        # create a system message
        system_message_content = assistant_config.guardrails_prompt
        system_message_content += f'\n\n{assistant_config.instruction_prompt}\n\nYour name is "{context.assistant.name}".'

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

        # Create a list of Message objects
        messages = [Message("system", system_message_content)]

        # get messages before the current message
        messages_response = await context.get_messages(before=message.id)
        history_messages = messages_response.messages + [message]

        # add conversation history
        for hist_message in history_messages:
            role = "assistant" if hist_message.sender.participant_id == context.assistant.id else "user"
            content = format_message(hist_message, participants_response.participants)
            messages.append(Message(role, content))

        # get the model adapter
        adapter = get_model_adapter(assistant_config.service_config.service_type)
        formatted_messages = adapter.format_messages(messages)

        try:
            # generate a response from the AI model
            content = await adapter.generate_response(formatted_messages, assistant_config)

            # merge the completion response into the passed in metadata
            metadata["debug"] = metadata.get("debug", {})
            metadata["debug"][method_metadata_key] = {
                "request": {
                    "model": getattr(assistant_config.service_config, f"{assistant_config.service_config.service_type.lower()}_model"),
                    "messages": formatted_messages,
                },
                "response": content,
            }
            assistant_config.request_config.response_tokens

        except Exception as e:
            logger.exception(f"exception occurred calling {assistant_config.service_config.service_type} chat completion: {e}")
            content = f"An error occurred while calling the {assistant_config.service_config.service_type} API. Is it configured correctly?"
            metadata["debug"] = metadata.get("debug", {})
            metadata["debug"][method_metadata_key] = {
                "request": {
                    "model": getattr(assistant_config.service_config, f"{assistant_config.service_config.service_type.lower()}_model"),
                    "messages": formatted_messages,
                },
                "error": str(e),
            }

        # set the message type based on the content
        message_type = MessageType.chat

        if content:
            # If content is a list, join it into a string
            if isinstance(content, list):
                content = ' '.join(content)

            # strip out the username from the response
            if content.startswith("["):
                content = re.sub(r"\[.*\]:\s", "", content)

            # check for the silence token
            if content.replace(" ", "") == silence_token:
                if assistant_config.enable_debug_output:
                    metadata["debug"][method_metadata_key]["silence_token"] = True
                    metadata["attribution"] = "debug output"
                    metadata["generated_content"] = False
                    await context.send_messages(
                        NewConversationMessage(
                            message_type=MessageType.notice,
                            content="[assistant chose to remain silent]",
                            metadata=metadata,
                        )
                    )
                return

            # override message type if content starts with "/", indicating a command response
            if content.startswith("/"):
                message_type = MessageType.command_response

        # send the response to the conversation
        await context.send_messages(
            NewConversationMessage(
                content=content or f"[no response from {assistant_config.service_config.service_type}]",
                message_type=message_type,
                metadata=metadata,
            )
        )

    finally:
        # update the participant status to indicate the assistant is done thinking
        await context.update_participant_me(UpdateParticipant(status=None))

def format_message(message: ConversationMessage, participants: list) -> str:
    conversation_participant = next(
        (participant for participant in participants if participant.id == message.sender.participant_id),
        None,
    )
    participant_name = conversation_participant.name if conversation_participant else "unknown"
    message_datetime = message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    return f"[{participant_name} - {message_datetime}]: {message.content}"


# this method is used to get the token count of a string.
def get_token_count(string: str) -> int:
    """
    Get the token count of a string.
    """
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(string))


# endregion
