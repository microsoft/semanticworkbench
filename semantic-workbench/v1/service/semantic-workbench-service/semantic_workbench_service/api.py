import logging
from contextlib import AsyncExitStack, asynccontextmanager
from typing import AsyncContextManager, AsyncGenerator, Callable

from fastapi import FastAPI

logger = logging.getLogger(__name__)


class FastAPILifespan:
    def __init__(self) -> None:
        self._lifecycle_handlers: list[Callable[[], AsyncContextManager[None]]] = []

    def register_handler(self, handler: Callable[[], AsyncContextManager[None]]) -> None:
        self._lifecycle_handlers.append(handler)

    @asynccontextmanager
    async def lifespan(self, app: FastAPI) -> AsyncGenerator[None, None]:
        async with AsyncExitStack() as stack:
            logger.debug("app lifespan starting up; title: %s, version: %s", app.title, app.version)

            for handler in self._lifecycle_handlers:
                await stack.enter_async_context(handler())

            logger.info("app lifespan started; title: %s, version: %s", app.title, app.version)

            try:
                yield
            finally:
                logger.debug("app lifespan shutting down; title: %s, version: %s", app.title, app.version)

        logger.info("app lifespan shut down; title: %s, version: %s", app.title, app.version)
