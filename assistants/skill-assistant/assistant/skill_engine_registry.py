import asyncio

from skill_library import Engine

from .logging import extra_data, logger
from .skill_event_mapper import SkillEventMapperProtocol


class SkillEngineRegistry:
    """
    This class handles the creation and management of skill engines for this
    service. Each conversation has its own assistant and we subscribe to each
    engine's events in a separate thread so that all events are able to be
    asynchronously passed on to the Semantic Workbench.
    """

    def __init__(self) -> None:
        self.engines: dict[str, Engine] = {}

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
        Define the skill engine that you want to have backing this service. You
        can configure the Skill Engine here.
        """

        logger.debug("Registering skill engine.", extra_data({"engine_id": engine.engine_id}))

        # Assistant event consumer.
        async def subscribe() -> None:
            """Event consumer for the skill engine."""
            logger.debug(
                "Event subscription started in SkillEngineRegistry.",
                extra_data({"engine_id": engine.engine_id}),
            )
            async for skill_event in engine.events:
                logger.debug("Event received in SkillEngineRegistry subscription.", extra_data({"event": skill_event}))
                try:
                    await event_mapper.map(skill_event)
                except Exception:
                    logger.exception("Exception in SkillEngineRegistry event handling.")

            # Hang out here until the assistant is stopped.
            await engine.wait()
            logger.debug(
                "Skill engine event subscription stopped in SkillEngineRegistry.",
                extra_data({"assistant_id": engine.engine_id}),
            )

        # Register the assistant.
        self.engines[engine.engine_id] = engine

        # Start an event consumer task and save a reference.
        asyncio.create_task(subscribe())

        return engine
