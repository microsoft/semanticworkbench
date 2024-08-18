import asyncio
import contextlib
import logging
import uuid
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import (
    IO,
    Any,
    AsyncContextManager,
    AsyncIterator,
    Callable,
    Generic,
    NoReturn,
    Optional,
    Protocol,
    Self,
    TypeVar,
)

import asgi_correlation_id
from fastapi import HTTPException, status
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, ValidationError
from semantic_workbench_api_model import assistant_model, workbench_model

from . import assistant_service, settings, storage

logger = logging.getLogger(__name__)


file_storage = storage.FileStorage(settings=settings.storage)


class AssistantConfigModel(ABC, BaseModel):
    model_config = ConfigDict(
        title="Assistant Configuration",
    )

    @abstractmethod
    def overwrite_defaults_from_env(self) -> Self: ...


AssistantConfigT = TypeVar("AssistantConfigT", bound=AssistantConfigModel)


class AssistantConfigStorage(Protocol, Generic[AssistantConfigT]):
    def get(self, assistant_id: str) -> AssistantConfigT: ...

    def get_with_defaults_overwritten_from_env(self, assistant_id: str) -> AssistantConfigT: ...

    def set(self, assistant_id: str, config: AssistantConfigT) -> None: ...

    def delete(self, assistant_id: str) -> None: ...

    def default_config_response_model(self) -> assistant_model.ConfigResponseModel: ...

    async def export_assistant_config(self, assistant_id: str) -> BaseModel: ...

    async def restore_assistant_config(self, assistant_id: str, from_export: IO[bytes]) -> None: ...

    async def get_config(self, assistant_id: str) -> assistant_model.ConfigResponseModel: ...

    async def update_config(
        self, assistant_id: str, updated_config: assistant_model.ConfigPutRequestModel
    ) -> assistant_model.ConfigResponseModel: ...


class SimpleAssistantConfigStorage(Generic[AssistantConfigT]):

    def __init__(
        self,
        cls: type[AssistantConfigT],
        ui_schema: dict[str, Any],
        default_config: AssistantConfigT | None = None,
        file_storage: storage.FileStorage = file_storage,
    ) -> None:
        self._default_config = default_config or cls()
        self._ui_schema = ui_schema
        self._storage = storage.ModelStorage[cls](
            cls=cls,
            file_storage=file_storage,
            namespace=f"configs_{cls.__name__}",
        )

    def get(self, assistant_id: str) -> AssistantConfigT:
        return self._storage.get(assistant_id) or self._default_config.model_copy()

    def get_with_defaults_overwritten_from_env(self, assistant_id: str) -> AssistantConfigT:
        config = self._storage.get(assistant_id) or self._default_config.model_copy()
        config = config.overwrite_defaults_from_env()
        return config

    def set(self, assistant_id: str, config: AssistantConfigT) -> None:
        self._storage[assistant_id] = config

    def delete(self, assistant_id: str) -> None:
        self._storage.delete(assistant_id)

    def default_config_response_model(self) -> assistant_model.ConfigResponseModel:
        return assistant_model.ConfigResponseModel(
            config=self._default_config.model_dump(),
            json_schema=self._default_config.model_json_schema(),
            ui_schema=self._ui_schema,
        )

    async def export_assistant_config(self, assistant_id: str) -> BaseModel:
        """Export the assistant's data - just config for now."""
        return self.get(assistant_id)

    async def restore_assistant_config(self, assistant_id: str, from_export: IO[bytes]) -> None:
        """Restore the assistant's data - just config for now."""
        config_json = from_export.read().decode("utf-8")
        restored_config = self._default_config.model_validate_json(config_json)
        self._storage.set(assistant_id, restored_config)

    async def get_config(self, assistant_id: str) -> assistant_model.ConfigResponseModel:
        assistant_config = self.get(assistant_id)
        return assistant_model.ConfigResponseModel(
            config=assistant_config.model_dump(),
            json_schema=assistant_config.model_json_schema(),
            ui_schema=self._ui_schema,
        )

    async def update_config(
        self, assistant_id: str, updated_config: assistant_model.ConfigPutRequestModel
    ) -> assistant_model.ConfigResponseModel:
        try:
            new_config = self._default_config.model_validate(updated_config.config)
        except ValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.errors())

        self.set(assistant_id, new_config)

        return await self.get_config(assistant_id)


class AssistantInstance(BaseModel):
    id: str
    assistant_name: str
    conversation_ids: set[str] = set()


class Event(BaseModel):
    assistant_id: str
    event: workbench_model.ConversationEvent


class AssistantBase(assistant_service.FastAPIAssistantService, Generic[AssistantConfigT], ABC):
    """
    A simple assistant service base class
    """

    def __init__(
        self,
        register_lifespan_handler: Callable[[Callable[[], AsyncContextManager[None]]], None],
        service_id: str,
        service_name: str,
        service_description: str,
        config_storage: AssistantConfigStorage[AssistantConfigT],
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
        self._config_storage = config_storage
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

    async def get_service_info(self) -> assistant_model.ServiceInfoModel:
        return assistant_model.ServiceInfoModel(
            assistant_service_id=self.service_id,
            name=self.service_name,
            description=self.service_description,
            default_config=self._config_storage.default_config_response_model(),
        )

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

    async def export_assistant_data(
        self, assistant_id: str
    ) -> StreamingResponse | FileResponse | JSONResponse | BaseModel:
        """Export the assistant's config."""
        return await self._config_storage.export_assistant_config(assistant_id)

    async def restore_assistant_data(self, assistant_id: str, from_export: IO[bytes]) -> None:
        """Import the assistant's config."""
        return await self._config_storage.restore_assistant_config(assistant_id, from_export)

    async def get_assistant(self, assistant_id: str) -> assistant_model.AssistantResponseModel:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        return assistant_model.AssistantResponseModel(id=instance.id)

    async def delete_assistant(self, assistant_id: str) -> None:
        self.assistant_instances.delete(assistant_id)
        self._config_storage.delete(assistant_id=assistant_id)

    async def get_config(self, assistant_id: str) -> assistant_model.ConfigResponseModel:
        return await self._config_storage.get_config(assistant_id=assistant_id)

    async def put_config(
        self, assistant_id: str, updated_config: assistant_model.ConfigPutRequestModel
    ) -> assistant_model.ConfigResponseModel:
        return await self._config_storage.update_config(assistant_id=assistant_id, updated_config=updated_config)

    async def get_conversation_state_descriptions(
        self, assistant_id: str, conversation_id: str
    ) -> assistant_model.StateDescriptionListResponseModel:
        """
        This method is used by the Semantic Workbench to create a list of
        "state" tabs. Overwrite as desired.
        """
        return assistant_model.StateDescriptionListResponseModel(states=[])

    async def get_conversation_state(
        self, assistant_id: str, conversation_id: str, state_id: str
    ) -> assistant_model.StateResponseModel:
        """
        This method is used by the Semantic Workbench to read the state of the
        assistant. This is generally useful for creating tabs in the Workbench.
        Override as desired.
        """
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    async def put_conversation_state(
        self,
        assistant_id: str,
        conversation_id: str,
        state_id: str,
        updated_state: assistant_model.StatePutRequestModel,
    ) -> assistant_model.StateResponseModel:
        """
        This method is used by the Semantic Workbench to put state into the
        assistant. This is generally useful for creating interactive tabs in the
        Workbench. Override as desired.
        """
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
