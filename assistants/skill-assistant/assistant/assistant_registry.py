import asyncio
import logging
from pathlib import Path
from typing import List

from chat_driver import ChatDriverConfig
from skill_library import Assistant, Skill

from assistant.skill_event_mapper import SkillEventMapperProtocol

logger = logging.getLogger(__name__)


# TODO: Put this registry in the skill library.
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

    async def get_or_create_assistant(
        self,
        assistant_id: str,
        event_mapper: SkillEventMapperProtocol,
        chat_driver_config: ChatDriverConfig,
        skills: List[Skill] = [],
    ) -> Assistant:
        """
        Get or create an assistant for the given conversation context.
        """
        assistant = self.get_assistant(assistant_id)
        if not assistant:
            assistant = await self.register_assistant(assistant_id, event_mapper, chat_driver_config, skills)
        return assistant

    def get_assistant(
        self,
        assistant_id: str,
    ) -> Assistant | None:
        if assistant_id in self.assistants:
            return self.assistants[assistant_id]
        return None

    async def register_assistant(
        self,
        assistant_id: str,
        event_mapper: SkillEventMapperProtocol,
        chat_driver_config: ChatDriverConfig,
        skills: List[Skill] = [],
    ) -> Assistant:
        """
        Define the skill assistant that you want to have backing this assistant
        service. You can configure the assistant instructions and which skills
        to include here.
        """

        # Create the assistant.
        assistant = Assistant(
            name="Assistant",
            assistant_id=assistant_id,
            drive_root=Path(".data") / assistant_id / "assistant",
            metadrive_drive_root=Path(".data") / assistant_id / ".assistant",
            chat_driver_config=chat_driver_config,
        )
        assistant.register_skills(skills)

        # Assistant event consumer.
        async def subscribe() -> None:
            """Event consumer for the assistant."""
            async for skill_event in assistant.events:
                try:
                    await event_mapper.map(skill_event)
                except Exception:
                    logging.exception("Exception in skill assistant event handling")
            await assistant.wait()

        # Register the assistant
        self.assistants[assistant_id] = assistant

        # Start an event consumer task and save a reference.
        task = asyncio.create_task(subscribe())
        self.tasks.add(task)

        # Remove the task from the set when it completes.
        task.add_done_callback(self.tasks.remove)

        return assistant
