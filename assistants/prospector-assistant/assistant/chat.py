# Copyright (c) Microsoft. All rights reserved.

# Prospector Assistant
#
# This assistant helps you mine ideas from artifacts.
#

import asyncio
import logging
import re
import traceback
from contextlib import asynccontextmanager
from typing import Any, Awaitable, Callable

import deepmerge
import openai_client
from assistant_extensions.ai_clients.model import CompletionMessageImageContent
from assistant_extensions.attachments import AttachmentsExtension
from content_safety.evaluators import CombinedContentSafetyEvaluator
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, ConfigDict
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
    BaseModelAssistantConfig,
    ContentSafety,
    ContentSafetyEvaluator,
    ConversationContext,
)

from . import legacy
from .agents.artifact_agent import Artifact, ArtifactAgent, ArtifactConversationInspectorStateProvider
from .agents.document_agent import DocumentAgent
from .artifact_creation_extension.extension import ArtifactCreationExtension
from .config import AssistantConfigModel
from .form_fill_extension import FormFillExtension, LLMConfig

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
    inspector_state_providers={
        "artifacts": ArtifactConversationInspectorStateProvider(assistant_config),
    },
)

attachments_extension = AttachmentsExtension(assistant)
form_fill_extension = FormFillExtension(assistant)
artifact_creation_extension = ArtifactCreationExtension(assistant, assistant_config)

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


@assistant.events.conversation.message.on_created
async def on_message_created(
    context: ConversationContext, event: ConversationEvent, message: ConversationMessage
) -> None:
    await legacy.provide_guidance_if_necessary(context)


@assistant.events.conversation.message.chat.on_created
async def on_chat_message_created(
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

    config = await assistant_config.get(context.assistant)
    if config.guided_workflow == "Long Document Creation":
        return

    # update the participant status to indicate the assistant is responding
    async with send_error_message_on_exception(context), context.set_status("responding..."):
        #
        # NOTE: we're experimenting with agents, if they are enabled, use them to respond to the conversation
        #
        metadata: dict[str, Any] = {"debug": {"content_safety": event.data.get(content_safety.metadata_key, {})}}

        match config.guided_workflow:
            case "Form Completion":
                await form_fill_execute(context, message)
            case "Document Creation":
                await create_document_execute(config, context, message, metadata)
            case _:
                logger.error("Guided workflow unknown or not supported.")


background_tasks: set[asyncio.Task] = set()


@assistant.events.conversation.on_created
async def on_conversation_created(context: ConversationContext) -> None:
    """
    Handle the event triggered when the assistant is added to a conversation.
    """
    assistant_sent_messages = await context.get_messages(participant_ids=[context.assistant.id], limit=1)
    welcome_sent_before = len(assistant_sent_messages.messages) > 0
    if welcome_sent_before:
        return

    #
    # NOTE: we're experimenting with agents, if they are enabled, use them to respond to the conversation
    #
    config = await assistant_config.get(context.assistant)
    metadata: dict[str, Any] = {"debug": {}}

    task: asyncio.Task | None = None
    match config.guided_workflow:
        case "Form Completion":
            task = asyncio.create_task(welcome_message_form_fill(context))
        case "Document Creation":
            task = asyncio.create_task(
                welcome_message_create_document(config, context, message=None, metadata=metadata)
            )
        case "Long Document Creation":
            pass
        case _:
            logger.error("Guided workflow unknown or not supported.")
            return

    if task:
        background_tasks.add(task)
        task.add_done_callback(background_tasks.remove)


async def welcome_message_form_fill(context: ConversationContext) -> None:
    async with send_error_message_on_exception(context), context.set_status("responding..."):
        await form_fill_execute(context, None)


async def welcome_message_create_document(
    config: AssistantConfigModel,
    context: ConversationContext,
    message: ConversationMessage | None,
    metadata: dict[str, Any],
) -> None:
    async with send_error_message_on_exception(context), context.set_status("responding..."):
        await create_document_execute(config, context, message, metadata)


@asynccontextmanager
async def send_error_message_on_exception(context: ConversationContext):
    try:
        yield
    except Exception as e:
        await context.send_messages(
            NewConversationMessage(
                content=f"An error occurred: {e}",
                message_type=MessageType.notice,
                metadata={"debug": {"stack_trace": traceback.format_exc()}},
            )
        )


# endregion

#
# region Form Fill Extension Helpers
#


async def form_fill_execute(context: ConversationContext, message: ConversationMessage | None) -> None:
    """
    Execute the form fill agent to respond to the conversation message.
    """
    config = await assistant_config.get(context.assistant)
    participants = await context.get_participants(include_inactive=True)
    await form_fill_extension.execute(
        llm_config=LLMConfig(
            openai_client_factory=lambda: openai_client.create_client(config.service_config),
            openai_model=config.request_config.openai_model,
            max_response_tokens=config.request_config.response_tokens,
        ),
        config=config.agents_config.form_fill_agent,
        context=context,
        latest_user_message=_format_message(message, participants.participants) if message else None,
        latest_attachment_filenames=message.filenames if message else [],
        get_attachment_content=form_fill_extension_get_attachment(context, config),
    )


def form_fill_extension_get_attachment(
    context: ConversationContext, config: AssistantConfigModel
) -> Callable[[str], Awaitable[str]]:
    """Helper function for the form_fill_extension to get the content of an attachment by filename."""

    async def get(filename: str) -> str:
        messages = await attachments_extension.get_completion_messages_for_attachments(
            context,
            config.agents_config.attachment_agent,
            include_filenames=[filename],
        )
        if not messages:
            return ""

        # filter down to the message with the attachment
        user_message = next(
            (message for message in messages if "<ATTACHMENT>" in str(message)),
            None,
        )
        if not user_message:
            return ""

        content = user_message.content
        match content:
            case str():
                return content

            case list():
                for part in content:
                    match part:
                        case CompletionMessageImageContent():
                            return part.data

        return ""

    return get


# endregion


#
# region Document Extension Helpers
#


async def create_document_execute(
    config: AssistantConfigModel,
    context: ConversationContext,
    message: ConversationMessage | None,
    metadata: dict[str, Any] = {},
) -> None:
    """
    Respond to a conversation message using the document agent.
    """
    # create the document agent instance
    document_agent = DocumentAgent(attachments_extension)
    await document_agent.create_document(config, context, message, metadata)


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

    # add the artifact agent instruction prompt to the system message content
    if config.agents_config.artifact_agent.enabled:
        system_message_content += f"\n\n{config.agents_config.artifact_agent.instruction_prompt}"

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
    completion_messages.extend(openai_client.convert_from_completion_messages(attachment_messages))

    # get messages before the current message
    messages_response = await context.get_messages(before=message.id)
    messages = messages_response.messages + [message]

    # calculate the token count for the messages so far
    token_count = openai_client.num_tokens_from_messages(
        model=config.request_config.openai_model, messages=completion_messages
    )

    # calculate the total available tokens for the response generation
    available_tokens = config.request_config.max_tokens - config.request_config.response_tokens

    # build the completion messages from the conversation history
    history_messages: list[ChatCompletionMessageParam] = []

    # add the messages in reverse order to get the most recent messages first
    for message in reversed(messages):
        messages_to_add: list[ChatCompletionMessageParam] = []

        # add the message to the completion messages, treating any message from a source other than the assistant
        # as a user message
        if message.sender.participant_id == context.assistant.id:
            messages_to_add.append({
                "role": "assistant",
                "content": _format_message(message, participants_response.participants),
            })
        else:
            # we are working with the messages in reverse order, so include any attachments before the message
            if message.filenames and len(message.filenames) > 0:
                # add a system message to indicate the attachments
                messages_to_add.append({
                    "role": "system",
                    "content": f"Attachment(s): {', '.join(message.filenames)}",
                })
            # add the user message to the completion messages
            messages_to_add.append({
                "role": "user",
                "content": _format_message(message, participants_response.participants),
            })

        # calculate the token count for the message and check if it exceeds the available tokens
        messages_to_add_token_count = openai_client.num_tokens_from_messages(
            model=config.request_config.openai_model, messages=messages_to_add
        )
        if (token_count + messages_to_add_token_count) > available_tokens:
            # stop processing messages if the token count exceeds the available tokens
            break

        token_count += messages_to_add_token_count
        history_messages.extend(messages_to_add)

    # reverse the history messages to get them back in the correct order
    history_messages.reverse()

    # add the history messages to the completion messages
    completion_messages.extend(history_messages)

    # initialize variables for the response content and total tokens used
    content: str | None = None
    completion_total_tokens: int | None = None

    # set default response message type
    message_type = MessageType.chat

    # TODO: DRY up this code by moving the OpenAI API call to a shared method and calling it from both branches
    # use structured response support to create or update artifacts, if artifacts are enabled
    if config.agents_config.artifact_agent.enabled:
        # define the structured response format for the AI model
        class StructuredResponseFormat(BaseModel):
            model_config = ConfigDict(
                extra="forbid",
                json_schema_extra={
                    "description": (
                        "The response format for the assistant. Use the assistant_response field for the"
                        " response content and the artifacts_to_create_or_update field for any artifacts"
                        " to create or update."
                    ),
                    "required": ["assistant_response", "artifacts_to_create_or_update"],
                },
            )

            assistant_response: str
            artifacts_to_create_or_update: list[Artifact]

        # generate a response from the AI model
        completion_total_tokens: int | None = None
        async with openai_client.create_client(config.service_config) as client:
            try:
                # call the OpenAI API to generate a completion
                completion = await client.beta.chat.completions.parse(
                    messages=completion_messages,
                    model=config.request_config.openai_model,
                    max_tokens=config.request_config.response_tokens,
                    response_format=StructuredResponseFormat,
                )
                content = completion.choices[0].message.content

                # get the prospector response from the completion
                structured_response = completion.choices[0].message.parsed
                # get the assistant response from the prospector response
                content = structured_response.assistant_response if structured_response else content
                # get the artifacts to create or update from the prospector response
                if structured_response and structured_response.artifacts_to_create_or_update:
                    for artifact in structured_response.artifacts_to_create_or_update:
                        ArtifactAgent.create_or_update_artifact(
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
                                    "messages": completion_messages,
                                    "max_tokens": config.request_config.response_tokens,
                                    "response_format": StructuredResponseFormat.model_json_schema(),
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
                                    "messages": completion_messages,
                                },
                                "error": str(e),
                            },
                        }
                    },
                )

    # fallback to prior approach to generate a response from the AI model when artifacts are not enabled
    if not config.agents_config.artifact_agent.enabled:
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
                                    "messages": completion_messages,
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
    if completion_total_tokens is not None and config.high_token_usage_warning.enabled:
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
