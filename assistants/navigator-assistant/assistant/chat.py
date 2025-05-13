# Copyright (c) Microsoft. All rights reserved.

# Prospector Assistant
#
# This assistant helps you mine ideas from artifacts.
#

import io
import logging
import pathlib
from typing import Any

import deepmerge
from assistant_extensions import attachments, dashboard_card, mcp, navigator
from content_safety.evaluators import CombinedContentSafetyEvaluator
from semantic_workbench_api_model.workbench_model import (
    ConversationEvent,
    ConversationMessage,
    MessageType,
    NewConversationMessage,
    ParticipantRole,
    UpdateParticipant,
)
from semantic_workbench_assistant.assistant_app import (
    AssistantApp,
    BaseModelAssistantConfig,
    ContentSafety,
    ContentSafetyEvaluator,
    ConversationContext,
)

from .config import AssistantConfigModel
from .response import respond_to_conversation
from .whiteboard import WhiteboardInspector

logger = logging.getLogger(__name__)

#
# region Setup
#

# the service id to be registered in the workbench to identify the assistant
service_id = "navigator-assistant.made-exploration-team"
# the name of the assistant service, as it will appear in the workbench UI
service_name = "Navigator Assistant"
# a description of the assistant service, as it will appear in the workbench UI
service_description = "An assistant for navigating the Semantic Workbench."

#
# create the configuration provider, using the extended configuration model
#
assistant_config = BaseModelAssistantConfig(AssistantConfigModel)


# define the content safety evaluator factory
async def content_evaluator_factory(context: ConversationContext) -> ContentSafetyEvaluator:
    config = await assistant_config.get(context.assistant)
    return CombinedContentSafetyEvaluator(config.content_safety_config)


content_safety = ContentSafety(content_evaluator_factory)


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
                background_color="rgb(238, 172, 178)",
                icon=dashboard_card.image_to_url(
                    pathlib.Path(__file__).parent / "assets" / "icon.svg", "image/svg+xml"
                ),
                card_content=dashboard_card.CardContent(
                    content_type="text/markdown",
                    content=(pathlib.Path(__file__).parent / "assets" / "card_content.md").read_text("utf-8"),
                ),
            )
        ),
        **navigator.metadata_for_assistant_navigator({
            "default": (pathlib.Path(__file__).parent / "text_includes" / "navigator_assistant_info.md").read_text(
                "utf-8"
            ),
        }),
    },
)


async def whiteboard_config_provider(ctx: ConversationContext) -> mcp.MCPServerConfig:
    config = await assistant_config.get(ctx.assistant)
    return config.tools.hosted_mcp_servers.memory_whiteboard


_ = WhiteboardInspector(state_id="whiteboard", app=assistant, server_config_provider=whiteboard_config_provider)


attachments_extension = attachments.AttachmentsExtension(assistant)

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
    async with context.set_status("thinking..."):
        config = await assistant_config.get(context.assistant)
        metadata: dict[str, Any] = {"debug": {"content_safety": event.data.get(content_safety.metadata_key, {})}}

        try:
            await respond_to_conversation(
                message=message,
                attachments_extension=attachments_extension,
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

    if message.sender.participant_role != ParticipantRole.user:
        # ignore messages that are not from the user
        return False

    # ignore messages that are directed at a participant other than this assistant
    if message.metadata.get("directed_at") and message.metadata["directed_at"] != context.assistant.id:
        return False

    # if configure to only respond to mentions, ignore messages where the content does not mention the assistant somewhere in the message
    if context.assistant.id not in message.metadata.get("mentions", []):
        # check to see if there are any other assistants in the conversation
        participant_list = await context.get_participants()
        other_assistants = [
            participant
            for participant in participant_list.participants
            if participant.role == "assistant" and participant.id != context.assistant.id
        ]
        if len(other_assistants) > 0:
            return False

    return True


@assistant.events.conversation.on_created
async def on_conversation_created(context: ConversationContext) -> None:
    """
    Handle the event triggered when the assistant is added to a conversation.
    """

    # hand the conversation off to the assistant if this conversation was spawned from another conversation
    conversation = await context.get_conversation()
    navigator_handoff = conversation.metadata.get("_navigator_handoff")

    assistant_sent_messages = await context.get_messages(participant_ids=[context.assistant.id], limit=1)
    assistant_has_sent_a_message = len(assistant_sent_messages.messages) > 0

    if navigator_handoff:
        if assistant_has_sent_a_message:
            return

        async with context.set_status("handing off..."):
            spawned_from_conversation_id = navigator_handoff.get("spawned_from_conversation_id")
            source_context = context.for_conversation(spawned_from_conversation_id)
            files_to_copy = navigator_handoff.get("files_to_copy")
            if files_to_copy:
                for filename in files_to_copy:
                    buffer = io.BytesIO()
                    file = await source_context.get_file(filename)
                    if not file:
                        continue

                    async with source_context.read_file(filename) as reader:
                        async for chunk in reader:
                            buffer.write(chunk)

                    await context.write_file(filename, buffer, file.content_type)

            introduction_message = navigator_handoff.get("introduction_message")
            await context.send_messages([
                NewConversationMessage(
                    content=introduction_message,
                    message_type=MessageType.chat,
                ),
                NewConversationMessage(
                    content=f"{context.assistant.name} left the conversation.",
                    message_type=MessageType.note,
                ),
            ])

        await context.update_participant_me(
            UpdateParticipant(
                active_participant=False,
            )
        )

        return

    participants_response = await context.get_participants()
    other_assistants_in_conversation = any(
        participant
        for participant in participants_response.participants
        if participant.role == ParticipantRole.assistant and participant.id != context.assistant.id
    )
    if other_assistants_in_conversation:
        return

    if assistant_has_sent_a_message:
        # don't send the welcome message if the assistant has already sent a message
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

    await context.update_participant_me(UpdateParticipant())


# endregion
