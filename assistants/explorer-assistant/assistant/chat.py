# Copyright (c) Microsoft. All rights reserved.

# Prospector Assistant
#
# This assistant helps you mine ideas from artifacts.
#

import logging
import re
import time
from typing import Any, Awaitable, Callable, Sequence

import deepmerge
import openai_client
from assistant_extensions.artifacts import ArtifactsExtension
from assistant_extensions.artifacts._model import ArtifactsConfigModel
from assistant_extensions.attachments import AttachmentsExtension
from assistant_extensions.workflows import WorkflowsConfigModel, WorkflowsExtension
from content_safety.evaluators import CombinedContentSafetyEvaluator
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ParsedChatCompletion,
)
from semantic_workbench_api_model.workbench_model import (
    AssistantStateEvent,
    ConversationEvent,
    ConversationMessage,
    ConversationParticipant,
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

        # Prospector assistant response
        await respond_to_conversation(context, config, metadata)


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

    # track the start time of the response generation
    response_start_time = time.time()

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

    # add the artifact agent instruction prompt to the system message content
    if config.extensions_config.artifacts.enabled:
        system_message_content += f"\n\n{config.extensions_config.artifacts.instruction_prompt}"

    # add the guardrails prompt to the system message content
    system_message_content += f"\n\n{config.guardrails_prompt}"

    # initialize the completion messages with the system message
    completion_messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": system_message_content,
        }
    ]

    # calculate the token count for the messages so far
    token_count = openai_client.num_tokens_from_messages(
        messages=completion_messages, model=config.request_config.openai_model
    )

    # generate the attachment messages from the attachment agent
    attachment_messages = await attachments_extension.get_completion_messages_for_attachments(
        context,
        config=config.extensions_config.attachments,
    )
    token_count += openai_client.num_tokens_from_messages(
        messages=attachment_messages, model=config.request_config.openai_model
    )

    # calculate the total available tokens for the response generation
    available_tokens = config.request_config.max_tokens - config.request_config.response_tokens

    history_messages = await _get_history_messages(
        context=context,
        participants=participants_response.participants,
        converter=_conversation_message_to_chat_completion_message_params,
        model=config.request_config.openai_model,
        token_limit=available_tokens - token_count,
    )

    # add the attachment messages to the completion messages, either inline or as separate messages
    if config.use_inline_attachments:
        # inject the attachment messages inline into the history messages
        history_messages = _inject_attachments_inline(history_messages, attachment_messages)
    else:
        # add the attachment messages to the completion messages before the history messages
        completion_messages.extend(attachment_messages)

    # add the history messages to the completion messages
    completion_messages.extend(history_messages)

    estimated_token_count = openai_client.num_tokens_from_messages(
        messages=completion_messages, model=config.request_config.openai_model
    )
    if estimated_token_count > config.request_config.max_tokens:
        await context.send_messages(
            NewConversationMessage(
                content=(
                    f"You've exceeded the token limit of {config.request_config.max_tokens} in this conversation ({estimated_token_count})."
                    " This assistant does not support recovery from this state."
                    " Please start a new conversation and let us know you ran into this."
                ),
                message_type=MessageType.chat,
            )
        )
        return

    # initialize variables for the response content and total tokens used
    content = ""
    completion_total_tokens = 0
    completion: ParsedChatCompletion | ChatCompletion | None = None

    # set default response message type
    message_type = MessageType.chat

    # generate a response from the AI model
    async with openai_client.create_client(config.service_config) as client:
        try:
            if config.request_config.is_reasoning_model:
                # convert all messages that use system role to user role as reasoning models do not support system role
                completion_messages = [
                    {
                        "role": "user",
                        "content": message["content"],
                    }
                    if message["role"] == "system"
                    else message
                    for message in completion_messages
                ]

                # for reasoning models, use max_completion_tokens instead of max_tokens
                completion = await client.chat.completions.create(
                    messages=completion_messages,
                    model=config.request_config.openai_model,
                    max_completion_tokens=config.request_config.response_tokens,
                )

            if config.extensions_config.artifacts.enabled:
                response = await artifacts_extension.get_openai_completion_response(
                    client,
                    completion_messages,
                    config.request_config.openai_model,
                    config.request_config.response_tokens,
                )

                completion = response.completion
                content = response.assistant_response
                artifacts_to_create_or_update = response.artifacts_to_create_or_update

                for artifact in artifacts_to_create_or_update:
                    artifacts_extension.create_or_update_artifact(
                        context,
                        artifact,
                    )
                # send an event to notify the artifact state was updated
                await context.send_conversation_state_event(
                    AssistantStateEvent(
                        state_id="artifacts",
                        event="updated",
                        state=None,
                    )
                )
                # send a focus event to notify the assistant to focus on the artifacts
                await context.send_conversation_state_event(
                    AssistantStateEvent(
                        state_id="artifacts",
                        event="focus",
                        state=None,
                    )
                )

            else:
                # call the OpenAI API to generate a completion
                try:
                    if config.request_config.is_reasoning_model:
                        # for reasoning models, use max_completion_tokens instead of max_tokens
                        completion = await client.chat.completions.create(
                            messages=completion_messages,
                            model=config.request_config.openai_model,
                            max_completion_tokens=config.request_config.response_tokens,
                        )
                    else:
                        completion = await client.chat.completions.create(
                            messages=completion_messages,
                            model=config.request_config.openai_model,
                            max_tokens=config.request_config.response_tokens,
                        )

                    content = completion.choices[0].message.content
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
                                        "messages": completion_messages,
                                    },
                                    "error": str(e),
                                },
                            }
                        },
                    )

            # create the footer items for the response
            footer_items = []

            if completion is not None:
                # get the total tokens used for the completion
                completion_total_tokens = completion.usage.total_tokens if completion.usage else 0
                footer_items.append(_get_token_usage_message(config.request_config.max_tokens, completion_total_tokens))

            # track the end time of the response generation
            response_end_time = time.time()
            response_duration = response_end_time - response_start_time

            # add the response duration to the footer items
            footer_items.append(_get_response_duration_message(response_duration))

            # update the metadata with debug information
            deepmerge.always_merger.merge(
                metadata,
                {
                    "debug": {
                        method_metadata_key: {
                            "request": {
                                "model": config.request_config.openai_model,
                                "messages": completion_messages,
                                "max_tokens": config.request_config.response_tokens,
                            },
                            "response": completion.model_dump() if completion else "[no response from openai]",
                        },
                    },
                    "footer_items": footer_items,
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
                                "messages": completion_messages,
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
    if completion_total_tokens and config.high_token_usage_warning.enabled:
        # calculate the token count for the warning threshold
        token_count_for_warning = config.request_config.max_tokens * (config.high_token_usage_warning.threshold / 100)

        # check if the completion total tokens exceed the warning threshold
        if completion_total_tokens > token_count_for_warning:
            content = f"{config.high_token_usage_warning.message}\n\nTotal tokens used: {completion_total_tokens}"

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

# TODO: move to a common module, such as either the openai_client or attachment module for easy re-use in other assistants


async def _conversation_message_to_chat_completion_message_params(
    context: ConversationContext, message: ConversationMessage, participants: list[ConversationParticipant]
) -> list[ChatCompletionMessageParam]:
    """
    Convert a conversation message to a list of chat completion message parameters.
    """

    # some messages may have multiple parts, such as a text message with an attachment
    chat_completion_messages: list[ChatCompletionMessageParam] = []

    # add the message to the completion messages, treating any message from a source other than the assistant
    # as a user message
    if message.sender.participant_id == context.assistant.id:
        chat_completion_messages.append({
            "role": "assistant",
            "content": _format_message(message, participants),
        })

    else:
        # add the user message to the completion messages
        chat_completion_messages.append({
            "role": "user",
            "content": _format_message(message, participants),
        })

        if message.filenames and len(message.filenames) > 0:
            # add a system message to indicate the attachments
            chat_completion_messages.append({
                "role": "system",
                "content": f"Attachment(s): {', '.join(message.filenames)}",
            })

    return chat_completion_messages


async def _get_history_messages(
    context: ConversationContext,
    participants: list[ConversationParticipant],
    converter: Callable[
        [ConversationContext, ConversationMessage, list[ConversationParticipant]],
        Awaitable[list[ChatCompletionMessageParam]],
    ],
    model: str,
    token_limit: int | None = None,
) -> list[ChatCompletionMessageParam]:
    """
    Get all messages in the conversation, formatted for use in a completion.
    """

    # each call to get_messages will return a maximum of 100 messages
    # so we need to loop until all messages are retrieved
    # if token_limit is provided, we will stop when the token limit is reached

    history = []
    token_count = 0
    before_message_id = None

    while True:
        # get the next batch of messages
        messages_response = await context.get_messages(limit=100, before=before_message_id)
        messages_list = messages_response.messages

        # if there are no more messages, break the loop
        if not messages_list or messages_list.count == 0:
            break

        # set the before_message_id for the next batch of messages
        before_message_id = messages_list[0].id

        # messages are returned in reverse order, so we need to reverse them
        for message in reversed(messages_list):
            # format the message
            formatted_message_list = await converter(context, message, participants)

            for formatted_message in formatted_message_list:
                # calculate the token count for the message
                try:
                    token_count += openai_client.num_tokens_from_message(model=model, message=formatted_message)
                except Exception as e:
                    logger.exception(f"exception occurred calculating token count: {e}")

            # if a token limit is provided and the token count exceeds the limit, break the loop
            if token_limit and token_count > token_limit:
                break

            # insert the formatted messages into the beginning of the history list
            history = formatted_message_list + history

    # return the formatted messages
    return history


def _inject_attachments_inline(
    history_messages: list[ChatCompletionMessageParam],
    attachment_messages: Sequence[ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam],
) -> list[ChatCompletionMessageParam]:
    """
    Inject the attachment messages inline into the history messages.
    """

    # iterate over the history messages and for every message that contains an attachment,
    # find the related attachment message and replace the attachment message with the inline attachment content
    for index, history_message in enumerate(history_messages):
        # if the history message does not contain content, as a string value, skip
        content = history_message.get("content")
        if not content or not isinstance(content, str):
            continue

        # get the attachment filenames string from the history message content
        attachment_filenames_string = re.findall(r"Attachment\(s\): (.+)", content)

        # if the history message does not contain an attachment filenames string, skip
        if not attachment_filenames_string:
            continue

        # split the attachment filenames string into a list of attachment filenames
        attachment_filenames = [filename.strip() for filename in attachment_filenames_string[0].split(",")]

        # initialize a list to store the replacement messages
        replacement_messages = []

        # iterate over the attachment filenames and find the related attachment message
        for attachment_filename in attachment_filenames:
            # find the related attachment message
            attachment_message = next(
                (
                    attachment_message
                    for attachment_message in attachment_messages
                    if f"<ATTACHMENT><FILENAME>{attachment_filename}</FILENAME>"
                    in str(attachment_message.get("content"))
                ),
                None,
            )

            if attachment_message:
                # replace the attachment message with the inline attachment content
                replacement_messages.append(attachment_message)

        # if there are replacement messages, replace the history message with the replacement messages
        if len(replacement_messages) > 0:
            history_messages[index : index + 1] = replacement_messages

    return history_messages


def _get_response_duration_message(response_duration: float) -> str:
    """
    Generate a display friendly message for the response duration, to be added to the footer items.
    """

    return f"Response time: {response_duration:.2f} seconds"


def _get_token_usage_message(
    max_tokens: int,
    completion_total_tokens: int,
) -> str:
    """
    Generate a display friendly message for the token usage, to be added to the footer items.
    """

    def get_display_count(tokens: int) -> str:
        # if less than 1k, return the number of tokens
        # if greater than or equal to 1k, return the number of tokens in k
        # use 1 decimal place for k
        # drop the decimal place if the number of tokens in k is a whole number
        if tokens < 1000:
            return str(tokens)
        else:
            tokens_in_k = tokens / 1000
            if tokens_in_k.is_integer():
                return f"{int(tokens_in_k)}k"
            else:
                return f"{tokens_in_k:.1f}k"

    return f"Tokens used: {get_display_count(completion_total_tokens)} of {get_display_count(max_tokens)} ({int(completion_total_tokens / max_tokens * 100)}%)"


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
