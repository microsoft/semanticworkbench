# Copyright (c) Microsoft. All rights reserved.

# An assistant for exploring use of the skills library, using the AssistantApp from
# the semantic-workbench-assistant package.

# The code in this module demonstrates the minimal code required to create a chat assistant
# using the AssistantApp class from the semantic-workbench-assistant package and leveraging
# the skills library to create a skill-based assistant.

from pathlib import Path
from typing import Any, Optional

import openai_client
from assistant_drive import Drive, DriveConfig
from common_skill import CommonSkillDefinition
from content_safety.evaluators import CombinedContentSafetyEvaluator
from guided_conversation_skill import GuidedConversationSkillDefinition
from openai_client.chat_driver import ChatDriverConfig
from posix_skill import PosixSkillDefinition
from semantic_workbench_api_model.workbench_model import (
    ConversationEvent,
    ConversationMessage,
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
from skill_library import Assistant
from skill_library.types import Metadata

from assistant.skill_event_mapper import SkillEventMapper

from .assistant_registry import AssistantRegistry
from .config import AssistantConfigModel
from .logging import logger

logger.info("Starting skill assistant service.")

#
# define the service ID, name, and description
#

# The service id to be registered in the workbench to identify the assistant.
service_id = "skill-assistant.made-exploration"

# The name of the assistant service, as it will appear in the workbench UI.
service_name = "Skill Assistant"

# A description of the assistant service, as it will appear in the workbench UI.
service_description = "A skills-based assistant using the Semantic Workbench Assistant SDK."

# Create the configuration provider, using the extended configuration model.
assistant_config = BaseModelAssistantConfig(AssistantConfigModel)


# Create the content safety interceptor.
async def content_evaluator_factory(conversation_context: ConversationContext) -> ContentSafetyEvaluator:
    config = await assistant_config.get(conversation_context.assistant)
    return CombinedContentSafetyEvaluator(config.content_safety_config)


content_safety = ContentSafety(content_evaluator_factory)


# create the AssistantApp instance
assistant_service = AssistantApp(
    assistant_service_id=service_id,
    assistant_service_name=service_name,
    assistant_service_description=service_description,
    config_provider=assistant_config.provider,
    content_interceptor=content_safety,
)

#
# create the FastAPI app instance
#
app = assistant_service.fastapi_app()


# The AssistantApp class provides a set of decorators for adding event handlers
# to respond to conversation events. In VS Code, typing "@assistant." (or the
# name of your AssistantApp instance) will show available events and methods.
#
# See the semantic-workbench-assistant AssistantApp class for more information
# on available events and methods. Examples:
# - @assistant.events.conversation.on_created (event triggered when the
#   assistant is added to a conversation)
# - @assistant.events.conversation.participant.on_created (event triggered when
#   a participant is added)
# - @assistant.events.conversation.message.on_created (event triggered when a
#   new message of any type is created)
# - @assistant.events.conversation.message.chat.on_created (event triggered when
#   a new chat message is created)

# This assistant registry is used to manage the assistants for this service and
# to register their event subscribers so we can map events to the workbench.
#
# NOTE: Currently, the skill assistant library doesn't have the notion of
# "conversations" so we map a skill library assistant to a particular
# conversation in the workbench. This means if you have a different conversation
# with the same "skill assistant" it will appear as a different assistant in the
# skill assistant library. We can improve this in the future by adding a
# conversation ID to the skill assistant library and mapping it to a
# conversation in the workbench.
assistant_registry = AssistantRegistry()


# Handle the event triggered when the assistant is added to a conversation.
@assistant_service.events.conversation.on_created
async def on_conversation_created(conversation_context: ConversationContext) -> None:
    """
    Handle the event triggered when the assistant is added to a conversation.
    """

    # send a welcome message to the conversation
    config = await assistant_config.get(conversation_context.assistant)
    welcome_message = config.welcome_message
    await conversation_context.send_messages(
        NewConversationMessage(
            content=welcome_message,
            message_type=MessageType.chat,
            metadata={"generated_content": False},
        )
    )


@assistant_service.events.conversation.message.chat.on_created
async def on_message_created(
    conversation_context: ConversationContext, event: ConversationEvent, message: ConversationMessage
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

    # Pass the message to the core response logic.
    async with conversation_context.set_status("thinking..."):
        config = await assistant_config.get(conversation_context.assistant)
        metadata: dict[str, Any] = {"debug": {"content_safety": event.data.get(content_safety.metadata_key, {})}}
        await respond_to_conversation(conversation_context, config, message, metadata)


@assistant_service.events.conversation.message.command.on_created
async def on_command_message_created(
    conversation_context: ConversationContext, event: ConversationEvent, message: ConversationMessage
) -> None:
    """
    Handle the event triggered when a new command message is created in the conversation.
    """

    # Pass the message to the core response logic. The skill library handles
    # commands, so we don't need to do anything here.
    async with conversation_context.set_status("thinking..."):
        config = await assistant_config.get(conversation_context.assistant)
        metadata: dict[str, Any] = {"debug": {"content_safety": event.data.get(content_safety.metadata_key, {})}}
        await respond_to_conversation(conversation_context, config, message, metadata)


# Core response logic for handling messages (chat or command) in the conversation.
async def respond_to_conversation(
    conversation_context: ConversationContext,
    config: AssistantConfigModel,
    message: ConversationMessage,
    metadata: Optional[Metadata] = None,
) -> None:
    """
    Respond to a conversation message.
    """
    assistant = await get_or_register_assistant(conversation_context, config)
    try:
        await assistant.put_message(message.content, metadata)
    except Exception as e:
        logger.exception("Exception in on_message_created.")
        await conversation_context.send_messages(
            NewConversationMessage(
                message_type=MessageType.note,
                content=f"Unhandled error: {e}",
            )
        )


# Get or register an assistant for the conversation.
async def get_or_register_assistant(
    conversation_context: ConversationContext, config: AssistantConfigModel
) -> Assistant:
    # Get an assistant from the registry.
    assistant_id = conversation_context.id
    assistant = assistant_registry.get_assistant(assistant_id)

    # Register an assistant if it's not there.
    if not assistant:
        assistant_drive_root = Path(".data") / assistant_id / "assistant"
        assistant_metadata_drive_root = Path(".data") / assistant_id / ".assistant"
        assistant_drive = Drive(DriveConfig(root=assistant_drive_root))
        language_model = openai_client.create_client(config.service_config)
        chat_driver_config = ChatDriverConfig(
            openai_client=language_model,
            model=config.chat_driver_config.openai_model,
            instructions=config.chat_driver_config.instructions,
        )

        assistant = Assistant(
            assistant_id=conversation_context.id,
            name="Assistant",
            chat_driver_config=chat_driver_config,
            drive_root=assistant_drive_root,
            metadata_drive_root=assistant_metadata_drive_root,
            skills=[
                CommonSkillDefinition(
                    name="common",
                    language_model=language_model,
                    drive=assistant_drive.subdrive("common"),
                    chat_driver_config=chat_driver_config,
                ),
                PosixSkillDefinition(
                    name="posix",
                    sandbox_dir=Path(".data") / conversation_context.id,
                    mount_dir="/mnt/data",
                    chat_driver_config=chat_driver_config,
                ),
                # FormFillerSkill(
                #     name="form_filler",
                #     chat_driver_config=chat_driver_config,
                #     language_model=language_model,
                # ),
                GuidedConversationSkillDefinition(
                    name="guided_conversation",
                    language_model=language_model,
                    drive=assistant_drive.subdrive("guided_conversation"),
                    chat_driver_config=chat_driver_config,
                ),
            ],
        )

        await assistant_registry.register_assistant(assistant, SkillEventMapper(conversation_context))

    return assistant
