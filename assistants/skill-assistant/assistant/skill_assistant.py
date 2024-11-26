# Copyright (c) Microsoft. All rights reserved.

# An assistant for exploring use of the skills library, using the AssistantApp from
# the semantic-workbench-assistant package.

# The code in this module demonstrates the minimal code required to create a chat assistant
# using the AssistantApp class from the semantic-workbench-assistant package and leveraging
# the skills library to create a skill-based assistant.

import logging
from pathlib import Path
from typing import Any, Optional

import openai_client
from assistant_drive import Drive, DriveConfig
from content_safety.evaluators import CombinedContentSafetyEvaluator
from form_filler_skill import FormFillerSkill
from form_filler_skill.guided_conversation import GuidedConversationSkill
from openai_client.chat_driver import ChatDriverConfig

# from form_filler_skill import FormFillerSkill
from posix_skill import PosixSkill
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
    ContentSafety,
    ContentSafetyEvaluator,
    ConversationContext,
)
from skill_library.types import Metadata

from assistant.skill_event_mapper import SkillEventMapper

from .assistant_registry import AssistantRegistry
from .config import AssistantConfigModel

logger = logging.getLogger(__name__)

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

#
# create the FastAPI app instance
#
app = assistant.fastapi_app()


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

assistant_registry = AssistantRegistry()


# Handle the event triggered when the assistant is added to a conversation.
@assistant.events.conversation.on_created
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


@assistant.events.conversation.message.chat.on_created
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

    # pass the message to the core response logic
    async with conversation_context.set_status("thinking..."):
        config = await assistant_config.get(conversation_context.assistant)
        metadata: dict[str, Any] = {"debug": {"content_safety": event.data.get(content_safety.metadata_key, {})}}
        await respond_to_conversation(conversation_context, config, message, metadata)


# @assistant.events.conversation.message.command.on_created
# async def on_command_message_created(
#     conversation_context: ConversationContext, event: ConversationEvent, message: ConversationMessage
# ) -> None:
#     """
#     Handle the event triggered when a new command message is created in the conversation.
#     """

#     # pass the message to the core response logic
#     async with conversation_context.set_status("thinking..."):
#         config = await assistant_config.get(conversation_context.assistant)
#         metadata: dict[str, Any] = {"debug": {"content_safety": event.data.get(content_safety.metadata_key, {})}}
#         await respond_to_conversation(conversation_context, config, message, metadata)


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

    # Update the participant status to indicate the assistant is thinking.
    await conversation_context.update_participant_me(UpdateParticipant(status="thinking..."))

    # Get an assistant from the skill library.
    assistant_id = conversation_context.id
    assistant = assistant_registry.get_assistant(assistant_id)
    drive_root = Path(".data") / assistant_id / "assistant"
    metadata_drive_root = Path(".data") / assistant_id / ".assistant"
    drive = Drive(DriveConfig(root=drive_root))

    # Create and register an assistant if necessary.
    if not assistant:
        try:
            language_model = openai_client.create_client(config.service_config)
            chat_driver_config = ChatDriverConfig(
                openai_client=language_model,
                model=config.chat_driver_config.openai_model,
                instructions=config.chat_driver_config.instructions,
            )
            assistant = await assistant_registry.register_assistant(
                conversation_context.id,
                SkillEventMapper(conversation_context),
                chat_driver_config,
                {
                    "posix": PosixSkill(
                        name="posix",
                        sandbox_dir=Path(".data") / conversation_context.id,
                        chat_driver_config=chat_driver_config,
                        mount_dir="/mnt/data",
                    ),
                    "form_filler": FormFillerSkill(
                        name="form_filler",
                        chat_driver_config=chat_driver_config,
                        language_model=language_model,
                    ),
                    "guided_conversation": GuidedConversationSkill(
                        name="guided_conversation",
                        language_model=language_model,
                        drive=drive.subdrive("guided_conversation"),
                        chat_driver_config=chat_driver_config,
                    ),
                },
                drive_root=drive_root,
                metadata_drive_root=metadata_drive_root,
            )

        except Exception as e:
            logging.exception("exception in on_message_created")
            await conversation_context.send_messages(
                NewConversationMessage(
                    message_type=MessageType.note,
                    content=f"Unhandled error: {e}",
                )
            )
            return
        finally:
            await conversation_context.update_participant_me(UpdateParticipant(status=None))

    try:
        await assistant.put_message(message.content, metadata)
    except Exception as e:
        logging.exception("exception in on_message_created")
        await conversation_context.send_messages(
            NewConversationMessage(
                message_type=MessageType.note,
                content=f"Unhandled error: {e}",
            )
        )
