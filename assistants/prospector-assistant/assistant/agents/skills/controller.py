import asyncio
import logging
from pathlib import Path

import openai_client
from chat_driver import ChatDriverConfig
from document_skill import DocumentSkillContext, DocumentSkill
from events import events as skill_events
from posix_skill import PosixSkill
from prospector_skill import ProspectorSkill
from semantic_workbench_api_model.workbench_model import (
    MessageType,
    NewConversationMessage,
    UpdateParticipant,
)
from semantic_workbench_assistant.assistant_app import (
    ConversationContext,
)
from skill_library import Assistant

from . import config as agent_config

logger = logging.getLogger(__name__)


async def _event_mapper(
    conversation_context: ConversationContext,
    skill_event: skill_events.EventProtocol,
) -> None:
    """
    Maps events emitted by the skill assistant (from running actions or
    routines) to message types understood by the Semantic Workbench.
    """
    metadata = {"debug": skill_event.metadata} if skill_event.metadata else None

    match skill_event:
        case skill_events.MessageEvent():
            await conversation_context.send_messages(
                NewConversationMessage(
                    content=skill_event.message or "",
                    metadata=metadata,
                )
            )

        case skill_events.InformationEvent():
            if skill_event.message:
                await conversation_context.send_messages(
                    NewConversationMessage(
                        content=f"Information event: {skill_event.message}",
                        message_type=MessageType.note,
                        metadata=metadata,
                    ),
                )

        case skill_events.ErrorEvent():
            await conversation_context.send_messages(
                NewConversationMessage(
                    content=skill_event.message or "",
                    metadata=metadata,
                )
            )

        case skill_events.StatusUpdatedEvent():
            await conversation_context.update_participant_me(UpdateParticipant(status=skill_event.message))

        case _:
            logger.warning("Unhandled event: %s", skill_event)


class AssistantRegistry:
    """
    This class handles the creation and management of skill assistant instances
    for this service. Each conversation has its own assistant and we start each
    assistant in it's own thread so that all events are able to be
    asynchronously passed on to the Semantic Workbench.

    """

    def __init__(self) -> None:
        self.assistants: dict[str, Assistant] = {}
        self.tasks: set[asyncio.Task] = set()

    async def get_assistant(
        self,
        conversation_context: ConversationContext,
        chat_driver_config: agent_config.ChatDriverConfig,
        service_config: openai_client.ServiceConfig,
    ) -> Assistant | None:
        # If the assistant already exists, return it.
        if conversation_context.id in self.assistants:
            return self.assistants[conversation_context.id]

        # Create a new assistant.
        assistant = await self.create_assistant(conversation_context, chat_driver_config, service_config)
        if not assistant:
            return

        async def subscribe() -> None:
            """Event consumer for the assistant."""
            async for skill_event in assistant.events:
                try:
                    await _event_mapper(conversation_context, skill_event)
                except Exception:
                    logging.exception("Exception in skill assistant event handling")
            await assistant.wait()

        # Register the assistant
        self.assistants[conversation_context.id] = assistant
        # Start an event consumer task and save a reference
        task = asyncio.create_task(subscribe())
        self.tasks.add(task)
        # Remove the task from the set when it completes
        task.add_done_callback(self.tasks.remove)

        return assistant

    async def create_assistant(
        self,
        conversation_context: ConversationContext,
        chat_driver_config: agent_config.ChatDriverConfig,
        service_config: openai_client.ServiceConfig,
    ) -> Assistant | None:
        """
        Define the skill assistant that you want to have backing this assistant
        service. You can configure the assistant instructions and which skills
        to include here.
        """
        # Get an OpenAI client.
        try:
            async_client = openai_client.create_client(service_config)
        except Exception as e:
            logging.exception("Failed to create OpenAI client")
            await conversation_context.send_messages(
                NewConversationMessage(message_type=MessageType.note, content=f"Could not create an OpenAI client: {e}")
            )
            return

        # Create the assistant.
        assistant = Assistant(
            name="Assistant",
            chat_driver_config=ChatDriverConfig(
                openai_client=async_client,
                model=chat_driver_config.openai_model,
                instructions=chat_driver_config.instructions,
            ),
            session_id=str(conversation_context.id),
        )

        # Define the skills this assistant should have.
        document_skill = DocumentSkill(
            # FIXME: This is a temporary solution to get the file to be saved - we need to implement a proper solution
            # context=assistant.context,
            context=DocumentSkillContext(),
            chat_driver_config=ChatDriverConfig(
                openai_client=async_client,
                model=chat_driver_config.openai_model,
            ),
        )

        posix_skill = PosixSkill(
            context=assistant.context,
            sandbox_dir=Path(".data"),
            mount_dir="/mnt/data",
            chat_driver_config=ChatDriverConfig(
                openai_client=async_client,
                model=chat_driver_config.openai_model,
            ),
        )

        prospector_skill = ProspectorSkill(
            context=assistant.context,
            chat_driver_config=ChatDriverConfig(
                openai_client=async_client,
                model=chat_driver_config.openai_model,
            ),
        )

        # Register the skills with the assistant.
        assistant.register_skills([document_skill, posix_skill, prospector_skill])

        return assistant
