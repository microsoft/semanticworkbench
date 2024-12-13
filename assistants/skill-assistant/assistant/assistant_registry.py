import asyncio
from os import PathLike
from pathlib import Path
from typing import Optional

from openai_client.chat_driver import ChatDriverConfig
from skill_library import Assistant, Skill

from .logging import extra_data, logger
from .skill_event_mapper import SkillEventMapperProtocol


class AssistantRegistry:
    """
    This class handles the creation and management of skill assistants for this
    service. Each conversation has its own assistant and we subscribe to each
    assistant's events in a separate thread so that all events are able to be
    asynchronously passed on to the Semantic Workbench.
    """

    def __init__(self) -> None:
        self.assistants: dict[str, Assistant] = {}
        # self.tasks: set[asyncio.Task] = set()

    async def get_or_register_assistant(
        self,
        assistant_id: str,
        event_mapper: SkillEventMapperProtocol,
        chat_driver_config: ChatDriverConfig,
        assistant_name: str = "Assistant",
        skills: Optional[dict[str, "Skill"]] = None,
        drive_root: PathLike | None = None,
        metadata_drive_root: PathLike | None = None,
    ) -> Assistant:
        """
        Get or create an assistant for the given conversation context.
        """
        assistant = self.get_assistant(assistant_id)
        if not assistant:
            assistant = await self.register_assistant(
                assistant_id,
                event_mapper,
                chat_driver_config,
                assistant_name,
                skills,
                drive_root,
                metadata_drive_root,
            )
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
        assistant_name: str = "Assistant",
        skills: dict[str, Skill] | None = None,
        drive_root: PathLike | None = None,
        metadata_drive_root: PathLike | None = None,
    ) -> Assistant:
        """
        Define the skill assistant that you want to have backing this assistant
        service. You can configure the assistant instructions and which skills
        to include here.
        """

        logger.debug("Registering assistant.", extra_data({"assistant_id": assistant_id}))

        # Create the assistant.
        assistant = Assistant(
            name=assistant_name,
            assistant_id=assistant_id,
            drive_root=drive_root or Path(".data") / assistant_id / "assistant",
            metadata_drive_root=metadata_drive_root or Path(".data") / assistant_id / ".assistant",
            chat_driver_config=chat_driver_config,
            skills=skills,
        )

        # Assistant event consumer.
        async def subscribe() -> None:
            """Event consumer for the assistant."""
            logger.debug(
                "Assistant event subscription started in the assistant registry.",
                extra_data({"assistant_id": assistant_id}),
            )
            async for skill_event in assistant.events:
                logger.debug(
                    "Assistant event received in assistant registry subscription.", extra_data({"event": skill_event})
                )
                try:
                    await event_mapper.map(skill_event)
                except Exception:
                    logger.exception("Exception in skill assistant event handling")

            # Hang out here until the assistant is stopped.
            await assistant.wait()
            logger.debug(
                "Assistant event subscription stopped in the assistant registry.",
                extra_data({"assistant_id": assistant_id}),
            )

        # Register the assistant.
        self.assistants[assistant_id] = assistant

        # Start an event consumer task and save a reference.
        # task = asyncio.create_task(subscribe())
        asyncio.create_task(subscribe())

        # Keep a reference to the task.
        # self.tasks.add(task)
        # task.add_done_callback(self.tasks.remove)

        return assistant
