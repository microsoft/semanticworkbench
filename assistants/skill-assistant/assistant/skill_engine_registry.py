import asyncio

from skill_library import Engine

from .logging import extra_data, logger
from .skill_event_mapper import SkillEventMapperProtocol


class SkillEngineRegistry:
    """
    This class handles the creation and management of skill assistants for this
    service. Each conversation has its own assistant and we subscribe to each
    assistant's events in a separate thread so that all events are able to be
    asynchronously passed on to the Semantic Workbench.
    """

    def __init__(self) -> None:
        self.engines: dict[str, Engine] = {}
        # self.tasks: set[asyncio.Task] = set()

    def get_engine(
        self,
        engine_id: str,
    ) -> Engine | None:
        if engine_id in self.engines:
            return self.engines[engine_id]
        return None

    async def register_engine(
        self,
        engine: Engine,
        event_mapper: SkillEventMapperProtocol,
    ) -> Engine:
        """
        Define the skill assistant that you want to have backing this assistant
        service. You can configure the assistant instructions and which skills
        to include here.
        """

        logger.debug("Registering assistant.", extra_data({"assistant_id": engine.engine_id}))

        # Assistant event consumer.
        async def subscribe() -> None:
            """Event consumer for the assistant."""
            logger.debug(
                "Assistant event subscription started in the assistant registry.",
                extra_data({"assistant_id": engine.engine_id}),
            )
            async for skill_event in engine.events:
                logger.debug(
                    "Assistant event received in assistant registry subscription.", extra_data({"event": skill_event})
                )
                try:
                    await event_mapper.map(skill_event)
                except Exception:
                    logger.exception("Exception in skill assistant event handling")

            # Hang out here until the assistant is stopped.
            await engine.wait()
            logger.debug(
                "Assistant event subscription stopped in the assistant registry.",
                extra_data({"assistant_id": engine.engine_id}),
            )

        # Register the assistant.
        self.engines[engine.engine_id] = engine

        # Start an event consumer task and save a reference.
        # task = asyncio.create_task(subscribe())
        asyncio.create_task(subscribe())

        # Keep a reference to the task.
        # self.tasks.add(task)
        # task.add_done_callback(self.tasks.remove)

        return engine
