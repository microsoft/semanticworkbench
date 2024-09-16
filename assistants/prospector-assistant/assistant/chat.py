# Copyright (c) Microsoft. All rights reserved.

# Prospector Assistant
#
# This assistant helps you mine ideas from artifacts.
#

import logging
import re
from typing import Any

import deepmerge
import tiktoken
from openai.types.chat import ChatCompletionMessageParam
from semantic_workbench_api_model.workbench_model import (
    ConversationEvent,
    ConversationMessage,
    ConversationParticipant,
    File,
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

from .agents.attachment_agent import AttachmentAgent
from .config import AssistantConfigModel, ui_schema
from .responsible_ai.azure_evaluator import AzureContentSafetyEvaluator
from .responsible_ai.openai_evaluator import (
    OpenAIContentSafetyEvaluator,
    OpenAIContentSafetyEvaluatorConfigModel,
)

logger = logging.getLogger(__name__)

#
# region Setup
#

# the service id to be registered in the workbench to identify the assistant
service_id = "prospector-assistant.made-exploration"
# the name of the assistant service, as it will appear in the workbench UI
service_name = "Prospector Assistant"
# a description of the assistant service, as it will appear in the workbench UI
service_description = "An assistant that helps you mine ideas from artifacts."

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
            message=message,
            metadata={"debug": {"content_safety": event.data.get(assistant.content_interceptor.metadata_key, {})}},
        )
    finally:
        # update the participant status to indicate the assistant is done thinking
        await context.update_participant_me(UpdateParticipant(status=None))


@assistant.events.conversation.on_created
async def on_conversation_created(context: ConversationContext) -> None:
    """
    Handle the event triggered when the assistant is added to a conversation.
    """

    # send a welcome message to the conversation
    assistant_config = await config_provider.get_typed(context.assistant)
    welcome_message = assistant_config.welcome_message
    await context.send_messages(
        NewConversationMessage(
            content=welcome_message,
            message_type=MessageType.chat,
            metadata={"generated_content": False},
        )
    )


@assistant.events.conversation.file.on_created
async def on_file_created(context: ConversationContext, event: ConversationEvent, file: File) -> None:
    """
    Handle the event triggered when a file is created in the conversation.
    """

    # update the participant status to indicate the assistant processing the new file
    await context.update_participant_me(UpdateParticipant(status=f"adding attachment '{file.filename}'..."))
    try:
        # process the file to create an attachment
        await create_or_update_attachment_from_file(
            context,
            file,
            metadata={"debug": {"content_safety": event.data.get(assistant.content_interceptor.metadata_key, {})}},
        )
    finally:
        # update the participant status to indicate the assistant is done processing the new file
        await context.update_participant_me(UpdateParticipant(status=None))


@assistant.events.conversation.file.on_updated
async def on_file_updated(context: ConversationContext, event: ConversationEvent, file: File) -> None:
    """
    Handle the event triggered when a file is updated in the conversation.
    """

    # update the participant status to indicate the assistant is updating the attachment
    await context.update_participant_me(UpdateParticipant(status=f"updating attachment '{file.filename}'..."))
    try:
        # process the file to update an attachment
        await create_or_update_attachment_from_file(
            context,
            file,
            metadata={"debug": {"content_safety": event.data.get(assistant.content_interceptor.metadata_key, {})}},
        )
    finally:
        # update the participant status to indicate the assistant is done updating the attachment
        await context.update_participant_me(UpdateParticipant(status=None))


@assistant.events.conversation.file.on_deleted
async def on_file_deleted(context: ConversationContext, event: ConversationEvent, file: File) -> None:
    """
    Handle the event triggered when a file is deleted in the conversation.
    """

    # update the participant status to indicate the assistant is deleting the attachment
    await context.update_participant_me(UpdateParticipant(status=f"deleting attachment '{file.filename}'..."))
    try:
        # delete the attachment for the file
        await delete_attachment_for_file(context, file)
    finally:
        # update the participant status to indicate the assistant is done deleting the attachment
        await context.update_participant_me(UpdateParticipant(status=None))


# endregion


#
# region Response
#


# demonstrates how to respond to a conversation message using the OpenAI API.
async def respond_to_conversation(
    context: ConversationContext, message: ConversationMessage, metadata: dict[str, Any] = {}
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

    # get the assistant's configuration, supports overwriting defaults from environment variables
    assistant_config = await config_provider.get_typed(context.assistant)

    # get the list of conversation participants
    participants_response = await context.get_participants(include_inactive=True)

    # establish a token to be used by the AI model to indicate no response
    silence_token = "{{SILENCE}}"

    system_message_content = f'{assistant_config.instruction_prompt}\n\nYour name is "{context.assistant.name}".'
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
    system_message_content += f"\n\n{assistant_config.guardrails_prompt}"

    completion_messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": system_message_content,
        }
    ]

    # add the attachment agent messages to the completion messages
    if assistant_config.agents_config.attachment_agent.include_in_response_generation:
        # generate the attachment messages from the attachment agent
        attachment_agent = AttachmentAgent()
        attachment_messages = await attachment_agent.generate_attachment_messages(context)

        # add the attachment messages to the completion messages
        if len(attachment_messages) > 0:
            completion_messages.append({
                "role": "system",
                "content": assistant_config.agents_config.attachment_agent.context_description,
            })
            completion_messages.extend(attachment_messages)

    # get messages before the current message
    messages_response = await context.get_messages(before=message.id)
    messages = messages_response.messages + [message]

    # calculate the token count for the messages so far
    token_count = 0
    for completion_message in completion_messages:
        content = completion_message.get("content")
        if isinstance(content, str):
            token_count += _get_token_count_for_str(content)

    # calculate the total available tokens for the response generation
    available_tokens = assistant_config.request_config.max_tokens - assistant_config.request_config.response_tokens

    # build the completion messages from the conversation history
    history_messages: list[ChatCompletionMessageParam] = []

    # add the messages in reverse order to get the most recent messages first
    for message in reversed(messages):
        # calculate the token count for the message and check if it exceeds the available tokens
        token_count += _get_token_count_for_str(_format_message(message, participants_response.participants))
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
        else:
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

    # generate a response from the AI model
    completion_total_tokens: int | None = None
    async with assistant_config.service_config.new_client(api_version="2024-06-01") as openai_client:
        try:
            # call the OpenAI API to generate a completion
            completion = await openai_client.chat.completions.create(
                messages=completion_messages,
                model=assistant_config.service_config.openai_model,
                max_tokens=assistant_config.request_config.response_tokens,
            )
            content = completion.choices[0].message.content

            # get the total tokens used for the completion
            completion_total_tokens = completion.usage.total_tokens if completion.usage else None

            # add the completion to the metadata for debugging
            deepmerge.always_merger.merge(
                metadata,
                {
                    "debug": {
                        f"{method_metadata_key}": {
                            "request": {
                                "model": assistant_config.service_config.openai_model,
                                "messages": completion_messages,
                                "max_tokens": assistant_config.request_config.response_tokens,
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
                "View the debug inspector for more information."
            )
            deepmerge.always_merger.merge(
                metadata,
                {
                    "debug": {
                        f"{method_metadata_key}": {
                            "request": {
                                "model": assistant_config.service_config.openai_model,
                                "messages": completion_messages,
                            },
                            "error": str(e),
                        },
                    }
                },
            )

    # set the message type based on the content
    message_type = MessageType.chat

    if content:
        # strip out the username from the response
        if content.startswith("["):
            content = re.sub(r"\[.*\]:\s", "", content)

        # model sometimes puts extra spaces in the response, so remove them
        # when checking for the silence token
        if content.replace(" ", "") == silence_token:
            # if debug output is enabled, notify the conversation that the assistant chose to remain silent
            if assistant_config.enable_debug_output:
                # add debug metadata to indicate the assistant chose to remain silent
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
    if completion_total_tokens is not None and assistant_config.high_token_usage_warning.enabled:
        # calculate the token count for the warning threshold
        token_count_for_warning = assistant_config.request_config.max_tokens * (
            assistant_config.high_token_usage_warning.threshold / 100
        )

        # check if the completion total tokens exceed the warning threshold
        if completion_total_tokens > token_count_for_warning:
            content = (
                f"{assistant_config.high_token_usage_warning.message}\n\nTotal tokens used: {completion_total_tokens}"
            )

            # send a notice message to the conversation that the token usage is high
            await context.send_messages(
                NewConversationMessage(
                    content=content,
                    message_type=MessageType.notice,
                    metadata={
                        "debug": {
                            "high_token_usage_warning": {
                                "completion_total_tokens": completion_total_tokens,
                                "threshold": assistant_config.high_token_usage_warning.threshold,
                                "token_count_for_warning": token_count_for_warning,
                            }
                        },
                        "attribution": "system",
                    },
                )
            )


# endregion


#
# region Attachments
#


async def create_or_update_attachment_from_file(
    context: ConversationContext, file: File, metadata: dict[str, Any] = {}
) -> None:
    """
    Create or update an attachment from a conversation file.
    """

    attachment_agent = AttachmentAgent()

    try:
        await attachment_agent.create_or_update_attachment_from_file(context, file, metadata)
    except Exception as e:
        logger.exception(f"exception occurred processing attachment: {e}")
        await context.send_messages(
            NewConversationMessage(
                content=f"There was an error processing the attachment ({file.filename}): {e}",
                message_type=MessageType.chat,
                metadata={**metadata, "attribution": "system"},
            )
        )


async def delete_attachment_for_file(context: ConversationContext, file: File, metadata: dict[str, Any] = {}) -> None:
    """
    Delete an attachment for a conversation file.
    """

    attachment_agent = AttachmentAgent()

    try:
        await attachment_agent.delete_attachment_for_file(context, file)
    except Exception as e:
        logger.exception(f"exception occurred deleting attachment: {e}")
        await context.send_messages(
            NewConversationMessage(
                content=f"There was an error deleting the attachment ({file.filename}): {e}",
                message_type=MessageType.chat,
                metadata={**metadata, "attribution": "system"},
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


def _get_token_count_for_str(string: str | list[str]) -> int:
    """
    Get the token count for a string or list of strings.
    """
    if isinstance(string, list):
        string = " ".join(string)

    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(string))


# endregion
