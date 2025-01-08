import asyncio

from skill_library import Assistant

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

    def get_assistant(
        self,
        assistant_id: str,
    ) -> Assistant | None:
        if assistant_id in self.assistants:
            return self.assistants[assistant_id]
        return None

    async def register_assistant(
        self,
        assistant: Assistant,
        event_mapper: SkillEventMapperProtocol,
    ) -> Assistant:
        """
        Define the skill assistant that you want to have backing this assistant
        service. You can configure the assistant instructions and which skills
        to include here.
        """

        logger.debug("Registering assistant.", extra_data({"assistant_id": assistant.assistant_id}))

        # Assistant event consumer.
        async def subscribe() -> None:
            """Event consumer for the assistant."""
            logger.debug(
                "Assistant event subscription started in the assistant registry.",
                extra_data({"assistant_id": assistant.assistant_id}),
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
                extra_data({"assistant_id": assistant.assistant_id}),
            )

        # Register the assistant.
        self.assistants[assistant.assistant_id] = assistant

        # Start an event consumer task and save a reference.
        # task = asyncio.create_task(subscribe())
        asyncio.create_task(subscribe())

        # Keep a reference to the task.
        # self.tasks.add(task)
        # task.add_done_callback(self.tasks.remove)

        return assistant
