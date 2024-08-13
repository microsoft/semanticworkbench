import asyncio
import contextlib
import logging
import uuid
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import IO, AsyncContextManager, AsyncIterator, Callable, NoReturn, Optional

import asgi_correlation_id
from fastapi import HTTPException, status
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
from semantic_workbench_api_model import assistant_model, workbench_model

from . import assistant_service, settings, storage

file_storage = storage.FileStorage(settings=settings.storage)

logger = logging.getLogger(__name__)


class AssistantInstance(BaseModel):
    id: str
    assistant_name: str
    conversation_ids: set[str] = set()


class Event(BaseModel):
    assistant_id: str
    event: workbench_model.ConversationEvent


class AssistantBase(assistant_service.FastAPIAssistantService, ABC):
    """
    A simple assistant service base class
    """

    def __init__(
        self,
        register_lifespan_handler: Callable[[Callable[[], AsyncContextManager[None]]], None],
        service_id: str,
        service_name: str,
        service_description: str,
    ) -> None:
        super().__init__(
            service_id=service_id,
            service_name=service_name,
            service_description=service_description,
            register_lifespan_handler=register_lifespan_handler,
        )
        self.assistant_instances = storage.ModelStorage[AssistantInstance](
            cls=AssistantInstance,
            file_storage=file_storage,
            namespace="instances",
        )
        self._event_queue_lock = asyncio.Lock()
        self._conversation_event_queues: dict[tuple[str, str], asyncio.Queue[Event]] = {}
        self._conversation_event_tasks: set[asyncio.Task] = set()
        register_lifespan_handler(self.lifespan)

    @asynccontextmanager
    async def lifespan(self) -> AsyncIterator[None]:
        try:
            yield
        finally:
            for task in self._conversation_event_tasks:
                task.cancel()

            with contextlib.suppress(asyncio.CancelledError):
                results = await asyncio.gather(*self._conversation_event_tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, BaseException):
                    logging.exception("event handling task raised exception", exc_info=result)

    async def _get_or_create_queue(self, assistant_id: str, conversation_id: str) -> asyncio.Queue[Event]:
        key = (assistant_id, conversation_id)
        async with self._event_queue_lock:
            queue = self._conversation_event_queues.get(key)
            if queue is not None:
                return queue

            queue = asyncio.Queue()
            self._conversation_event_queues[key] = queue
            task = asyncio.create_task(self._handle_events(queue))
            self._conversation_event_tasks.add(task)
            task.add_done_callback(self._conversation_event_tasks.discard)
            return queue

    @abstractmethod
    async def get_service_info(self) -> assistant_model.ServiceInfoModel:
        pass

    async def put_assistant(
        self,
        assistant_id: str,
        assistant: assistant_model.AssistantPutRequestModel,
        from_export: Optional[IO[bytes]] = None,
    ) -> assistant_model.AssistantResponseModel:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            instance = AssistantInstance(
                id=assistant_id,
                assistant_name=assistant.assistant_name,
            )

        instance.assistant_name = assistant.assistant_name

        if from_export is not None:
            await self.restore_assistant_data(assistant_id=assistant_id, from_export=from_export)

        self.assistant_instances.set(assistant_id, instance)
        return await self.get_assistant(assistant_id=assistant_id)

    @abstractmethod
    async def export_assistant_data(
        self, assistant_id: str
    ) -> StreamingResponse | FileResponse | JSONResponse | BaseModel:
        pass

    @abstractmethod
    async def restore_assistant_data(self, assistant_id: str, from_export: IO[bytes]) -> None:
        pass

    async def get_assistant(self, assistant_id: str) -> assistant_model.AssistantResponseModel:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        return assistant_model.AssistantResponseModel(id=instance.id)

    async def delete_assistant(self, assistant_id: str) -> None:
        self.assistant_instances.delete(assistant_id)

    @abstractmethod
    async def get_config(self, assistant_id: str) -> assistant_model.ConfigResponseModel:
        pass

    @abstractmethod
    async def put_config(
        self, assistant_id: str, updated_config: assistant_model.ConfigPutRequestModel
    ) -> assistant_model.ConfigResponseModel:
        pass

    async def get_conversation_state_descriptions(
        self, assistant_id: str, conversation_id: str
    ) -> assistant_model.StateDescriptionListResponseModel:
        return assistant_model.StateDescriptionListResponseModel(states=[])

    async def get_conversation_state(
        self, assistant_id: str, conversation_id: str, state_id: str
    ) -> assistant_model.StateResponseModel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    async def put_conversation_state(
        self,
        assistant_id: str,
        conversation_id: str,
        state_id: str,
        updated_state: assistant_model.StatePutRequestModel,
    ) -> assistant_model.StateResponseModel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    async def put_conversation(
        self,
        assistant_id: str,
        conversation_id: str,
        request: assistant_model.ConversationPutRequestModel,
        from_export: IO[bytes] | None = None,
    ) -> assistant_model.ConversationResponseModel:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        # Send an event if this is a new conversation.
        is_new_conversation = conversation_id not in instance.conversation_ids
        if not is_new_conversation:
            return await self.get_conversation(assistant_id=assistant_id, conversation_id=conversation_id)

        instance.conversation_ids.add(conversation_id)
        self.assistant_instances.set(assistant_id, instance)

        if from_export is not None:
            await self.restore_conversation_data(
                assistant_id=assistant_id, conversation_id=conversation_id, from_export=from_export
            )

        await self.post_conversation_event(
            assistant_id=assistant_id,
            conversation_id=conversation_id,
            event=workbench_model.ConversationEvent(
                conversation_id=uuid.UUID(conversation_id),
                event=workbench_model.ConversationEventType.conversation_created,
                data={},
            ),
        )

        return await self.get_conversation(assistant_id=assistant_id, conversation_id=conversation_id)

    async def export_conversation_data(self, assistant_id: str, conversation_id: str) -> JSONResponse:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        if conversation_id not in instance.conversation_ids:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        return JSONResponse({})

    async def restore_conversation_data(self, assistant_id: str, conversation_id: str, from_export: IO[bytes]) -> None:
        pass

    async def get_conversation(
        self, assistant_id: str, conversation_id: str
    ) -> assistant_model.ConversationResponseModel:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        if conversation_id not in instance.conversation_ids:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        return assistant_model.ConversationResponseModel(id=conversation_id)

    async def delete_conversation(self, assistant_id: str, conversation_id: str) -> None:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        if conversation_id not in instance.conversation_ids:
            return

        instance.conversation_ids.remove(conversation_id)
        self.assistant_instances.set(assistant_id, instance)

        await self.post_conversation_event(
            assistant_id=assistant_id,
            conversation_id=conversation_id,
            event=workbench_model.ConversationEvent(
                conversation_id=uuid.UUID(conversation_id),
                event=workbench_model.ConversationEventType.conversation_deleted,
                data={},
            ),
        )

    async def post_conversation_event(
        self, assistant_id: str, conversation_id: str, event: workbench_model.ConversationEvent
    ) -> None:
        """
        Receives events from semantic workbench and buffers them in a queue to avoid keeping
        the workbench waiting.
        """
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        if conversation_id not in instance.conversation_ids:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        logger.debug(
            "received conversation event; assistant_id: %s, conversation_id: %s, event: %s",
            assistant_id,
            conversation_id,
            event,
        )

        queue = await self._get_or_create_queue(assistant_id=assistant_id, conversation_id=conversation_id)
        await queue.put(Event(assistant_id=assistant_id, event=event))

    async def _handle_events(self, queue: asyncio.Queue[Event]) -> NoReturn:
        """
        De-queues events and makes the call to process_workbench_event.
        """
        while True:
            try:
                try:
                    async with asyncio.timeout(1):
                        wrapper = await queue.get()
                except asyncio.TimeoutError:
                    continue

                queue.task_done()

                asgi_correlation_id.correlation_id.set(wrapper.event.correlation_id)

                instance = self.assistant_instances.get(wrapper.assistant_id)
                if instance is None:
                    continue

                event = wrapper.event

                if str(event.conversation_id) not in instance.conversation_ids:
                    continue

                await self.on_workbench_event(assistant_instance=instance, event=event)

            except Exception:
                logging.exception("exception in _forward_events loop")

    @abstractmethod
    async def on_workbench_event(
        self,
        assistant_instance: AssistantInstance,
        event: workbench_model.ConversationEvent,
    ) -> None:
        """
        Override this method to handle events from the workbench.
        """
        pass