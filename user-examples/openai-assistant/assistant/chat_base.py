import asyncio
import contextlib
import logging
import uuid
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import (
    IO,
    Annotated,
    Any,
    AsyncContextManager,
    AsyncIterator,
    Callable,
    Generic,
    NoReturn,
    Optional,
    Self,
    TypeVar,
)

import asgi_correlation_id
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from semantic_workbench_api_model import assistant_model, workbench_model
from semantic_workbench_assistant import assistant_service, config, storage

from . import file_storage

logger = logging.getLogger(__name__)


class ConfigModelBase(BaseModel):
    model_config = ConfigDict(title="Assistant Configuration")

    persona_prompt: Annotated[
        str,
        Field(
            title="Persona Prompt",
            description="The prompt used to define the persona of the AI assistant.",
        ),
    ] = "You are an AI assistant that helps people with their work."

    # FIXME: This name is confusing as it implies that the config values
    # are being overwritten from the environment, but it's actually
    # overwriting just the default values with the environment values.
    # The user configured values are not overwritten.
    def overwrite_from_env(self) -> Self:
        """
        Overwrite string fields that currently have their default values. Values are
        overwritten with values from environment variables or .env file. If a field
        is a BaseModel, it will be recursively updated.
        """
        updated = config.overwrite_defaults_from_env(self, prefix="assistant", separator="__")
        return updated


class ConversationModel(assistant_model.ConversationResponseModel):
    pass


ConfigT = TypeVar("ConfigT", bound=ConfigModelBase)


class AssistantInstance(BaseModel, Generic[ConfigT]):
    id: str
    assistant_name: str
    config: ConfigT
    conversations: dict[str, ConversationModel] = {}

    # this field is no longer used - it is kept for backwards compatibility
    _deprecated_workbench_base_url: Annotated[str, Field(alias="workbench_base_url")] = ""


class Event(BaseModel):
    assistant_id: str
    event: workbench_model.ConversationEvent


class ChatAssistantBase(assistant_service.FastAPIAssistantService, Generic[ConfigT], ABC):
    """
    A simple assistant service base class
    """

    def __init__(
        self,
        register_lifespan_handler: Callable[[Callable[[], AsyncContextManager[None]]], None],
        instance_cls: type[AssistantInstance[ConfigT]],
        config_cls: type[ConfigT],
        config_ui_schema: dict[str, Any],
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
        self.config_cls = config_cls
        self.config_ui_schema = config_ui_schema
        self.assistant_instances = storage.ModelStorage[AssistantInstance[ConfigT]](
            cls=instance_cls,
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

    async def get_service_info(self) -> assistant_model.ServiceInfoModel:
        return assistant_model.ServiceInfoModel(
            assistant_service_id=self.service_id,
            name=self.service_name,
            description=self.service_description,
            default_config=assistant_model.ConfigResponseModel(
                config=self.config_cls().model_dump(),
                json_schema=self.config_cls.model_json_schema(),
                ui_schema=self.config_ui_schema,
            ),
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
                config=self.config_cls(),
            )

        instance.assistant_name = assistant.assistant_name

        if from_export is not None:
            config_json = from_export.read().decode("utf-8")
            instance.config = self.config_cls.model_validate_json(config_json)

        self.assistant_instances.set(assistant_id, instance)
        return await self.get_assistant(assistant_id=assistant_id)

    async def export_assistant_data(self, assistant_id: str) -> BaseModel:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        return instance.config

    async def get_assistant(self, assistant_id: str) -> assistant_model.AssistantResponseModel:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        return assistant_model.AssistantResponseModel(id=instance.id)

    async def delete_assistant(self, assistant_id: str) -> None:
        self.assistant_instances.delete(assistant_id)

    async def get_config(self, assistant_id: str) -> assistant_model.ConfigResponseModel:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        return assistant_model.ConfigResponseModel(
            config=instance.config.model_dump(),
            json_schema=instance.config.model_json_schema(),
            ui_schema=self.config_ui_schema,
        )

    async def put_config(
        self, assistant_id: str, updated_config: assistant_model.ConfigPutRequestModel
    ) -> assistant_model.ConfigResponseModel:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        try:
            config = self.config_cls.model_validate(updated_config.config, strict=True)
        except ValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.errors())

        instance.config = config
        self.assistant_instances.set(assistant_id, instance)

        return await self.get_config(assistant_id=assistant_id)

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
        from_export: Optional[IO[bytes]] = None,
    ) -> assistant_model.ConversationResponseModel:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        conversation = ConversationModel(
            id=conversation_id,
        )

        # Send an event if this is a new conversation.
        is_new_conversation = conversation_id not in instance.conversations

        instance.conversations[conversation_id] = conversation
        self.assistant_instances.set(assistant_id, instance)

        if is_new_conversation:
            await self.post_conversation_event(
                assistant_id=assistant_id,
                conversation_id=conversation_id,
                event=workbench_model.ConversationEvent(
                    conversation_id=uuid.UUID(conversation_id),
                    event=workbench_model.ConversationEventType.conversation_created,
                    data={},
                ),
            )

        return conversation

    async def export_conversation_data(self, assistant_id: str, conversation_id: str) -> JSONResponse:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        conversation = instance.conversations.get(conversation_id)
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        return JSONResponse({})

    async def get_conversation(
        self, assistant_id: str, conversation_id: str
    ) -> assistant_model.ConversationResponseModel:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        conversation = instance.conversations.get(conversation_id)
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        return conversation

    async def delete_conversation(self, assistant_id: str, conversation_id: str) -> None:
        instance = self.assistant_instances.get(assistant_id)
        if instance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        instance.conversations.pop(conversation_id, None)
        self.assistant_instances.set(assistant_id, instance)

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
        conversation = instance.conversations.get(conversation_id)
        if conversation is None:
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

                conversation = instance.conversations.get(str(event.conversation_id))
                if conversation is None:
                    continue

                await self.process_workbench_event(assistant_instance=instance, conversation=conversation, event=event)

            except Exception:
                logging.exception("exception in _forward_events loop")

    @abstractmethod
    async def process_workbench_event(
        self,
        assistant_instance: AssistantInstance[ConfigT],
        conversation: ConversationModel,
        event: workbench_model.ConversationEvent,
    ) -> None:
        """
        Override this method to handle events from the workbench.
        """
        pass
