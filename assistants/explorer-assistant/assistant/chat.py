# Copyright (c) Microsoft. All rights reserved.

# Prospector Assistant
#
# This assistant helps you mine ideas from artifacts.
#

import logging
import re
from typing import Any

import deepmerge
import openai_client
from assistant_extensions.attachments import AttachmentsExtension
from content_safety.evaluators import CombinedContentSafetyEvaluator
from openai.types.chat import ChatCompletionMessageParam
from semantic_workbench_api_model.workbench_model import (
    ConversationEvent,
    ConversationMessage,
    ConversationParticipant,
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

from .config import AssistantConfigModel

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

    # ignore messages from this assistant
    if message.sender.participant_id == context.assistant.id:
        return

    # update the participant status to indicate the assistant is thinking
    async with context.set_status_for_block("thinking..."):
        config = await assistant_config.get(context.assistant)
        metadata: dict[str, Any] = {"debug": {"content_safety": event.data.get(content_safety.metadata_key, {})}}

        # Prospector assistant response
        await respond_to_conversation(context, config, message, metadata)


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


#
# region Response
#


# demonstrates how to respond to a conversation message using the OpenAI API.
async def respond_to_conversation(
    context: ConversationContext,
    config: AssistantConfigModel,
    message: ConversationMessage,
    metadata: dict[str, Any] = {},
) -> None:
    """
    Respond to a conversation message.

    This method uses the OpenAI API to generate a response to the message.

    It includes any attachments as individual system messages before the chat history, along with references
    to the attachments in the point in the conversation where they were mentioned. This allows the model to
    consider the full contents of the attachments separate from the conversation, but with the context of
    where they were mentioned and any relevant surrounding context such as how to interpret the attachment
    or why it was shared or what to do with it.
    """

    # define the metadata key for any metadata created within this method
    method_metadata_key = "respond_to_conversation"

    # get the list of conversation participants
    participants_response = await context.get_participants(include_inactive=True)

    # establish a token to be used by the AI model to indicate no response
    silence_token = "{{SILENCE}}"

    system_message_content = f'{config.instruction_prompt}\n\nYour name is "{context.assistant.name}".'
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

    # add the guardrails prompt to the system message content
    system_message_content += f"\n\n{config.guardrails_prompt}"

    completion_messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": system_message_content,
        }
    ]

    # generate the attachment messages from the attachment agent
    attachment_messages = await attachments_extension.get_completion_messages_for_attachments(
        context, config=config.agents_config.attachment_agent
    )

    # add the attachment messages to the completion messages
    completion_messages.extend(attachment_messages)

    # get messages before the current message
    messages_response = await context.get_messages(before=message.id)
    messages = messages_response.messages + [message]

    # calculate the token count for the messages so far
    token_count = 0
    for completion_message in completion_messages:
        completion_message_content = completion_message.get("content")
        if isinstance(completion_message_content, str):
            token_count += openai_client.count_tokens(
                model=config.request_config.openai_model, value=completion_message_content
            )

    # calculate the total available tokens for the response generation
    available_tokens = config.request_config.max_tokens - config.request_config.response_tokens

    # build the completion messages from the conversation history
    history_messages: list[ChatCompletionMessageParam] = []

    # add the messages in reverse order to get the most recent messages first
    for message in reversed(messages):
        # calculate the token count for the message and check if it exceeds the available tokens
        token_count += openai_client.count_tokens(
            model=config.request_config.openai_model, value=_format_message(message, participants_response.participants)
        )
        if token_count > available_tokens:
            # stop processing messages if the token count exceeds the available tokens
            break

        # add the message to the completion messages, treating any message from a source other than the assistant
        # as a user message
        if message.sender.participant_id == context.assistant.id:
            history_messages.append({
                "role": "assistant",
                "content": _format_message(message, participants_response.participants),
            })
            continue

        # we are working with the messages in reverse order, so include any attachments before the message
        if message.filenames and len(message.filenames) > 0:
            # add a system message to indicate the attachments
            history_messages.append({
                "role": "system",
                "content": f"Attachment(s): {', '.join(message.filenames)}",
            })
        # add the user message to the completion messages
        history_messages.append({
            "role": "user",
            "content": _format_message(message, participants_response.participants),
        })

    # reverse the history messages to get them back in the correct order
    history_messages.reverse()

    # add the history messages to the completion messages
    completion_messages.extend(history_messages)

    # initialize variables for the response content and total tokens used
    content: str | None = None
    completion_total_tokens: int | None = None

    # set default response message type
    message_type = MessageType.chat

    # generate a response from the AI model
    completion_total_tokens: int | None = None
    async with openai_client.create_client(config.service_config) as client:
        try:
            # call the OpenAI API to generate a completion
            completion = await client.chat.completions.create(
                messages=completion_messages,
                model=config.request_config.openai_model,
                max_tokens=config.request_config.response_tokens,
            )
            content = completion.choices[0].message.content

            # get the total tokens used for the completion
            completion_total_tokens = completion.usage.total_tokens if completion.usage else None

            # add the completion to the metadata for debugging
            deepmerge.always_merger.merge(
                metadata,
                {
                    "debug": {
                        method_metadata_key: {
                            "request": {
                                "model": config.request_config.openai_model,
                                "messages": openai_client.truncate_messages_for_logging(completion_messages),
                                "max_tokens": config.request_config.response_tokens,
                            },
                            "response": completion.model_dump() if completion else "[no response from openai]",
                        },
                    }
                },
            )

        except Exception as e:
            logger.exception(f"exception occurred calling openai chat completion: {e}")
            content = (
                "An error occurred while calling the OpenAI API. Is it configured correctly?"
                " View the debug inspector for more information."
            )
            message_type = MessageType.notice
            deepmerge.always_merger.merge(
                metadata,
                {
                    "debug": {
                        method_metadata_key: {
                            "request": {
                                "model": config.request_config.openai_model,
                                "messages": openai_client.truncate_messages_for_logging(completion_messages),
                            },
                            "error": str(e),
                        },
                    }
                },
            )

    if content:
        # strip out the username from the response
        if content.startswith("["):
            content = re.sub(r"\[.*\]:\s", "", content)

        # model sometimes puts extra spaces in the response, so remove them
        # when checking for the silence token
        if content.replace(" ", "") == silence_token:
            # if debug output is enabled, notify the conversation that the assistant chose to remain silent
            if config.enable_debug_output:
                # add debug metadata to indicate the assistant chose to remain silent
                deepmerge.always_merger.merge(
                    metadata,
                    {
                        "debug": {
                            method_metadata_key: {
                                "silence_token": True,
                            },
                        },
                        "attribution": "debug output",
                        "generated_content": False,
                    },
                )
                # send a notice message to the conversation
                await context.send_messages(
                    NewConversationMessage(
                        message_type=MessageType.notice,
                        content="[assistant chose to remain silent]",
                        metadata=metadata,
                    )
                )
            return

        # override message type if content starts with /
        if content.startswith("/"):
            message_type = MessageType.command_response

    # send the response to the conversation
    await context.send_messages(
        NewConversationMessage(
            content=content or "[no response from openai]",
            message_type=message_type,
            metadata=metadata,
        )
    )

    # check the token usage and send a warning if it is high
    if completion_total_tokens is not None and config.high_token_usage_warning.enabled:
        # calculate the token count for the warning threshold
        token_count_for_warning = config.request_config.max_tokens * (config.high_token_usage_warning.threshold / 100)

        # check if the completion total tokens exceed the warning threshold
        if completion_total_tokens > token_count_for_warning:
            content = f"{config.high_token_usage_warning.message}\n\n" f"Total tokens used: {completion_total_tokens}"

            # send a notice message to the conversation that the token usage is high
            await context.send_messages(
                NewConversationMessage(
                    content=content,
                    message_type=MessageType.notice,
                    metadata={
                        "debug": {
                            "high_token_usage_warning": {
                                "completion_total_tokens": completion_total_tokens,
                                "threshold": config.high_token_usage_warning.threshold,
                                "token_count_for_warning": token_count_for_warning,
                            }
                        },
                        "attribution": "system",
                    },
                )
            )


# endregion


#
# region Helpers
#


def _format_message(message: ConversationMessage, participants: list[ConversationParticipant]) -> str:
    """
    Format a conversation message for display.
    """
    conversation_participant = next(
        (participant for participant in participants if participant.id == message.sender.participant_id),
        None,
    )
    participant_name = conversation_participant.name if conversation_participant else "unknown"
    message_datetime = message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    return f"[{participant_name} - {message_datetime}]: {message.content}"


# endregion
