import asyncio
import contextlib
import functools
import logging
import pathlib
from contextlib import asynccontextmanager, contextmanager
from typing import (
    IO,
    AsyncContextManager,
    AsyncIterator,
    Callable,
    TypeVar,
    cast,
)

import asgi_correlation_id
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ValidationError
from semantic_workbench_api_model import assistant_model, workbench_model

from .. import settings
from ..assistant_service import FastAPIAssistantService
from ..storage import read_model, write_model
from .context import AssistantContext, ConversationContext
from .error import BadRequestError, ConflictError, NotFoundError
from .protocol import (
    AssistantAppProtocol,
    WriteableAssistantConversationInspectorStateProvider,
)

logger = logging.getLogger(__name__)


class _ConversationState(BaseModel):
    """
    Private model for conversation state for the AssistantService.
    """

    conversation_id: str
    title: str


class _AssistantState(BaseModel):
    """
    Private model for assistant state for the AssistantService.
    """

    assistant_id: str
    assistant_name: str

    template_id: str = "default"

    conversations: dict[str, _ConversationState] = {}


class _PersistedAssistantStates(BaseModel):
    """
    Private model for persisted assistant states for the AssistantService.
    """

    assistants: dict[str, _AssistantState] = {}


class _Event(BaseModel):
    assistant_id: str
    event: workbench_model.ConversationEvent


def translate_assistant_errors(func):
    @contextmanager
    def wrapping_logic():
        try:
            yield

        except ConflictError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

        except NotFoundError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

        except BadRequestError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        # all others are allowed through, likely resulting in 500s

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not asyncio.iscoroutinefunction(func):
            with wrapping_logic():
                return func(*args, **kwargs)

        async def tmp():
            with wrapping_logic():
                return await func(*args, **kwargs)

        return tmp()

    return wrapper


ValueT = TypeVar("ValueT")


def require_found(value: ValueT | None, message: str | None = None) -> ValueT:
    if value is None:
        raise NotFoundError(message)
    return value


class AssistantService(FastAPIAssistantService):
    """
    Semantic workbench assistant-service that wraps an AssistantApp, handling API requests from the semantic-workbench
    service. It is responsible for the persistence of assistant and conversation instances and delegates all other
    responsibilities to the AssistantApp.
    """

    def __init__(
        self,
        assistant_app: AssistantAppProtocol,
        register_lifespan_handler: Callable[[Callable[[], AsyncContextManager[None]]], None],
    ) -> None:
        self.assistant_app = assistant_app

        super().__init__(
            service_id=self.assistant_app.assistant_service_id,
            service_name=self.assistant_app.assistant_service_name,
            service_description=self.assistant_app.assistant_service_description,
            register_lifespan_handler=register_lifespan_handler,
        )

        self._root_path = pathlib.Path(settings.storage.root)
        self._assistant_states_path = self._root_path / "assistant_states.json"
        self._event_queue_lock = asyncio.Lock()
        self._conversation_event_queues: dict[tuple[str, str], asyncio.Queue[_Event]] = {}
        self._conversation_event_tasks: set[asyncio.Task] = set()
        register_lifespan_handler(self.lifespan)

    @asynccontextmanager
    async def lifespan(self) -> AsyncIterator[None]:
        await self.assistant_app.events._on_service_start_handlers(True)

        try:
            yield
        finally:
            await self.assistant_app.events._on_service_shutdown_handlers(True)

            for task in self._conversation_event_tasks:
                task.cancel()

            results = []
            with contextlib.suppress(asyncio.CancelledError):
                results = await asyncio.gather(*self._conversation_event_tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    logging.exception("event handling task raised exception", exc_info=result)

    def read_assistant_states(self) -> _PersistedAssistantStates:
        states = None
        try:
            states = read_model(self._assistant_states_path, _PersistedAssistantStates)
        except FileNotFoundError:
            pass
        except ValidationError:
            logging.warning(
                "invalid assistant states, returning new state; path: %s",
                self._assistant_states_path,
                exc_info=True,
            )

        return states or _PersistedAssistantStates()

    def write_assistant_states(self, new_states: _PersistedAssistantStates) -> None:
        write_model(self._assistant_states_path, new_states)

    def _build_assistant_context(self, assistant_id: str, template_id: str, assistant_name: str) -> AssistantContext:
        return AssistantContext(
            _assistant_service_id=self.service_id,
            _template_id=template_id,
            id=assistant_id,
            name=assistant_name,
        )

    def get_assistant_context(self, assistant_id: str) -> AssistantContext | None:
        states = self.read_assistant_states()
        assistant_state = states.assistants.get(assistant_id)
        if assistant_state is None:
            return None
        return self._build_assistant_context(
            assistant_state.assistant_id,
            assistant_state.template_id,
            assistant_state.assistant_name,
        )

    def get_conversation_context(self, assistant_id: str, conversation_id: str) -> ConversationContext | None:
        states = self.read_assistant_states()
        assistant_state = states.assistants.get(assistant_id)
        if assistant_state is None:
            return None
        conversation_state = assistant_state.conversations.get(conversation_id)
        if conversation_state is None:
            return None

        assistant_context = self._build_assistant_context(
            assistant_id, assistant_state.template_id, assistant_state.assistant_name
        )
        context = ConversationContext(
            assistant=assistant_context,
            id=conversation_state.conversation_id,
            title=conversation_state.title,
        )

        content_interceptor = self.assistant_app.content_interceptor
        if content_interceptor is not None:
            original_send_messages = context.send_messages

            async def override(
                messages: workbench_model.NewConversationMessage | list[workbench_model.NewConversationMessage],
            ) -> workbench_model.ConversationMessageList:
                try:
                    if not isinstance(messages, list):
                        messages = [messages]
                    updated_messages = await content_interceptor.intercept_outgoing_messages(context, messages)
                except Exception:
                    logger.exception("error in content interceptor, swallowing messages")
                    return workbench_model.ConversationMessageList(messages=[])

                return await original_send_messages(updated_messages)

            context.send_messages = override

        return context

    @translate_assistant_errors
    async def get_service_info(self) -> assistant_model.ServiceInfoModel:
        return assistant_model.ServiceInfoModel(
            assistant_service_id=self.service_id,
            name=self.service_name,
            templates=[
                assistant_model.AssistantTemplateModel(
                    id=template.id,
                    name=template.name,
                    description=template.description,
                    config=assistant_model.ConfigResponseModel(
                        config=self.assistant_app.config_provider.default_for(template.id).config,
                        errors=[],
                        json_schema=self.assistant_app.config_provider.default_for(template.id).json_schema,
                        ui_schema=self.assistant_app.config_provider.default_for(template.id).ui_schema,
                    ),
                )
                for template in self.assistant_app.templates.values()
            ],
            metadata=self.assistant_app.assistant_service_metadata,
        )

    @translate_assistant_errors
    async def put_assistant(
        self,
        assistant_id: str,
        assistant: assistant_model.AssistantPutRequestModel,
        from_export: IO[bytes] | None = None,
    ) -> assistant_model.AssistantResponseModel:
        is_new = False
        states = self.read_assistant_states()

        assistant_state = states.assistants.get(assistant_id) or _AssistantState(
            assistant_id=assistant_id,
            assistant_name=assistant.assistant_name,
            template_id=assistant.template_id,
        )
        assistant_state.assistant_name = assistant.assistant_name

        is_new = not from_export and assistant_id not in states.assistants
        states.assistants[assistant_id] = assistant_state
        self.write_assistant_states(states)

        assistant_context = require_found(self.get_assistant_context(assistant_id))
        if is_new:
            await self.assistant_app.events.assistant._on_created_handlers(True, assistant_context)
        else:
            await self.assistant_app.events.assistant._on_updated_handlers(True, assistant_context)

        if from_export is not None:
            await self.assistant_app.data_exporter.import_(assistant_context, from_export)

        return await self.get_assistant(assistant_id)

    @translate_assistant_errors
    async def export_assistant_data(self, assistant_id: str) -> StreamingResponse:
        assistant_context = require_found(self.get_assistant_context(assistant_id))

        async def iterate_stream() -> AsyncIterator[bytes]:
            async with self.assistant_app.data_exporter.export(assistant_context) as stream:
                for chunk in stream:
                    yield chunk

        return StreamingResponse(content=iterate_stream())

    @translate_assistant_errors
    async def get_assistant(self, assistant_id: str) -> assistant_model.AssistantResponseModel:
        assistant_context = require_found(self.get_assistant_context(assistant_id))
        return assistant_model.AssistantResponseModel(id=assistant_context.id)

    @translate_assistant_errors
    async def delete_assistant(self, assistant_id: str) -> None:
        assistant_context = self.get_assistant_context(assistant_id)
        if assistant_context is None:
            return

        states = self.read_assistant_states()
        assistant_state = states.assistants.get(assistant_id)

        if assistant_state is None:
            return

        # delete conversations
        for conversation_id in assistant_state.conversations:
            await self.delete_conversation(assistant_id, conversation_id)

        states = self.read_assistant_states()
        states.assistants.pop(assistant_id, None)
        self.write_assistant_states(states)

        await self.assistant_app.events.assistant._on_deleted_handlers(True, assistant_context)

    @translate_assistant_errors
    async def get_config(self, assistant_id: str) -> assistant_model.ConfigResponseModel:
        assistant_context = require_found(self.get_assistant_context(assistant_id))

        config = await self.assistant_app.config_provider.get(assistant_context)
        return assistant_model.ConfigResponseModel(
            config=config.config,
            errors=config.errors,
            json_schema=config.json_schema,
            ui_schema=config.ui_schema,
        )

    @translate_assistant_errors
    async def put_config(
        self, assistant_id: str, updated_config: assistant_model.ConfigPutRequestModel
    ) -> assistant_model.ConfigResponseModel:
        assistant_context = require_found(self.get_assistant_context(assistant_id))

        await self.assistant_app.config_provider.set(assistant_context, updated_config.config)
        return await self.get_config(assistant_id)

    @translate_assistant_errors
    async def put_conversation(
        self,
        assistant_id: str,
        conversation_id: str,
        conversation: assistant_model.ConversationPutRequestModel,
        from_export: IO[bytes] | None = None,
    ) -> assistant_model.ConversationResponseModel:
        states = self.read_assistant_states()
        assistant_state = require_found(states.assistants.get(assistant_id))

        conversation_state = assistant_state.conversations.get(conversation_id) or _ConversationState(
            conversation_id=conversation_id,
            title=conversation.title,
        )
        is_new = conversation_id not in assistant_state.conversations

        conversation_state.title = conversation.title

        assistant_state.conversations[conversation_id] = conversation_state
        self.write_assistant_states(states)

        conversation_context = require_found(self.get_conversation_context(assistant_id, conversation_id))

        if is_new:
            await self.assistant_app.events.conversation._on_created_handlers(not from_export, conversation_context)
        else:
            await self.assistant_app.events.conversation._on_updated_handlers(True, conversation_context)

        if from_export is not None:
            await self.assistant_app.conversation_data_exporter.import_(conversation_context, from_export)

        return assistant_model.ConversationResponseModel(id=conversation_context.id)

    @translate_assistant_errors
    async def export_conversation_data(self, assistant_id: str, conversation_id: str) -> StreamingResponse:
        conversation_context = require_found(self.get_conversation_context(assistant_id, conversation_id))

        async def iterate_stream() -> AsyncIterator[bytes]:
            async with self.assistant_app.conversation_data_exporter.export(conversation_context) as stream:
                for chunk in stream:
                    yield chunk

        return StreamingResponse(content=iterate_stream())

    @translate_assistant_errors
    async def get_conversation(
        self, assistant_id: str, conversation_id: str
    ) -> assistant_model.ConversationResponseModel:
        conversation_context = require_found(self.get_conversation_context(assistant_id, conversation_id))
        return assistant_model.ConversationResponseModel(id=conversation_context.id)

    @translate_assistant_errors
    async def delete_conversation(self, assistant_id: str, conversation_id: str) -> None:
        conversation_context = self.get_conversation_context(assistant_id, conversation_id)
        if conversation_context is None:
            return None

        states = self.read_assistant_states()
        assistant_state = require_found(states.assistants.get(assistant_id))
        if assistant_state.conversations.pop(conversation_id, None) is None:
            return
        self.write_assistant_states(states)

        await self.assistant_app.events.conversation._on_deleted_handlers(True, conversation_context)

    async def _get_or_create_queue(self, assistant_id: str, conversation_id: str) -> asyncio.Queue[_Event]:
        key = (assistant_id, conversation_id)
        async with self._event_queue_lock:
            queue = self._conversation_event_queues.get(key)
            if queue is not None:
                return queue

            queue = asyncio.Queue()
            self._conversation_event_queues[key] = queue
            task = asyncio.create_task(self._forward_events_from_queue(queue))
            self._conversation_event_tasks.add(task)
            task.add_done_callback(self._conversation_event_tasks.discard)
            return queue

    async def _forward_events_from_queue(self, queue: asyncio.Queue[_Event]) -> None:
        """
        De-queues events and makes the call to process_workbench_event.
        """
        while True:
            try:
                wrapper = None
                try:
                    async with asyncio.timeout(1):
                        wrapper = await queue.get()
                except asyncio.TimeoutError:
                    continue

                except RuntimeError as e:
                    logging.exception("exception in _forward_events_from_queue loop")
                    if e.args[0] == "Event loop is closed":
                        break

                queue.task_done()

                if wrapper is None:
                    continue

                assistant_id = wrapper.assistant_id
                event = wrapper.event

                asgi_correlation_id.correlation_id.set(event.correlation_id)

                conversation_context = self.get_conversation_context(
                    assistant_id=assistant_id,
                    conversation_id=str(event.conversation_id),
                )
                if conversation_context is None:
                    continue

                await self._forward_event(conversation_context, event)

            except Exception:
                logging.exception("exception in _forward_events_from_queue loop")

    @translate_assistant_errors
    async def post_conversation_event(
        self,
        assistant_id: str,
        conversation_id: str,
        event: workbench_model.ConversationEvent,
    ) -> None:
        """
        Receives events from semantic workbench and buffers them in a queue to avoid keeping
        the workbench waiting.
        """
        _ = require_found(self.get_conversation_context(assistant_id, conversation_id))

        queue = await self._get_or_create_queue(assistant_id=assistant_id, conversation_id=conversation_id)
        await queue.put(_Event(assistant_id=assistant_id, event=event))

    async def _forward_event(
        self,
        conversation_context: ConversationContext,
        event: workbench_model.ConversationEvent,
    ) -> None:
        updated_event = event

        content_interceptor = self.assistant_app.content_interceptor
        if content_interceptor is not None:
            try:
                updated_event = await content_interceptor.intercept_incoming_event(conversation_context, event)
            except Exception:
                logger.exception("error in content interceptor, dropping event")

            if updated_event is None:
                logger.info(
                    "event was dropped by content interceptor; event: %s, interceptor: %s",
                    event.event,
                    content_interceptor.__class__.__name__,
                )
                return

        match updated_event.event:
            case workbench_model.ConversationEventType.message_created:
                try:
                    message = workbench_model.ConversationMessage.model_validate(updated_event.data.get("message", {}))
                except ValidationError:
                    logging.exception("invalid message event data")
                    return

                event_originated_externally = message.sender.participant_id != conversation_context.assistant.id

                async with asyncio.TaskGroup() as tg:
                    tg.create_task(
                        self.assistant_app.events.conversation.message._on_created_handlers(
                            event_originated_externally,
                            conversation_context,
                            updated_event,
                            message,
                        )
                    )
                    tg.create_task(
                        self.assistant_app.events.conversation.message[message.message_type]._on_created_handlers(
                            event_originated_externally,
                            conversation_context,
                            updated_event,
                            message,
                        )
                    )

            case workbench_model.ConversationEventType.message_deleted:
                try:
                    message = workbench_model.ConversationMessage.model_validate(updated_event.data.get("message", {}))
                except ValidationError:
                    logging.exception("invalid message event data")
                    return

                event_originated_externally = message.sender.participant_id != conversation_context.assistant.id

                async with asyncio.TaskGroup() as tg:
                    tg.create_task(
                        self.assistant_app.events.conversation.message._on_deleted_handlers(
                            event_originated_externally,
                            conversation_context,
                            updated_event,
                            message,
                        )
                    )
                    tg.create_task(
                        self.assistant_app.events.conversation.message[message.message_type]._on_deleted_handlers(
                            event_originated_externally,
                            conversation_context,
                            updated_event,
                            message,
                        )
                    )

            case workbench_model.ConversationEventType.participant_created:
                try:
                    participant = workbench_model.ConversationParticipant.model_validate(
                        updated_event.data.get("participant", {})
                    )
                except ValidationError:
                    logging.exception("invalid participant event data")
                    return

                event_originated_externally = participant.id != conversation_context.assistant.id
                await self.assistant_app.events.conversation.participant._on_created_handlers(
                    event_originated_externally,
                    conversation_context,
                    updated_event,
                    participant,
                )

            case workbench_model.ConversationEventType.participant_updated:
                try:
                    participant = workbench_model.ConversationParticipant.model_validate(
                        updated_event.data.get("participant", {})
                    )
                except ValidationError:
                    logging.exception("invalid participant event data")
                    return

                event_originated_externally = participant.id != conversation_context.assistant.id
                await self.assistant_app.events.conversation.participant._on_updated_handlers(
                    event_originated_externally,
                    conversation_context,
                    updated_event,
                    participant,
                )

            case workbench_model.ConversationEventType.file_created:
                try:
                    file = workbench_model.File.model_validate(updated_event.data.get("file", {}))
                except ValidationError:
                    logging.exception("invalid file event data")
                    return

                event_originated_externally = file.participant_id != conversation_context.assistant.id
                await self.assistant_app.events.conversation.file._on_created_handlers(
                    event_originated_externally,
                    conversation_context,
                    updated_event,
                    file,
                )

            case workbench_model.ConversationEventType.file_updated:
                try:
                    file = workbench_model.File.model_validate(updated_event.data.get("file", {}))
                except ValidationError:
                    logging.exception("invalid file event data")
                    return

                event_originated_externally = file.participant_id != conversation_context.assistant.id
                await self.assistant_app.events.conversation.file._on_updated_handlers(
                    event_originated_externally,
                    conversation_context,
                    updated_event,
                    file,
                )

            case workbench_model.ConversationEventType.file_deleted:
                try:
                    file = workbench_model.File.model_validate(updated_event.data.get("file", {}))
                except ValidationError:
                    logging.exception("invalid file event data")
                    return

                event_originated_externally = file.participant_id != conversation_context.assistant.id
                await self.assistant_app.events.conversation.file._on_deleted_handlers(
                    event_originated_externally,
                    conversation_context,
                    updated_event,
                    file,
                )

    @translate_assistant_errors
    async def get_conversation_state_descriptions(
        self, assistant_id: str, conversation_id: str
    ) -> assistant_model.StateDescriptionListResponseModel:
        require_found(self.get_conversation_context(assistant_id, conversation_id))
        return assistant_model.StateDescriptionListResponseModel(
            states=[
                assistant_model.StateDescriptionResponseModel(
                    id=id,
                    display_name=provider.display_name,
                    description=provider.description,
                )
                for id, provider in self.assistant_app.inspector_state_providers.items()
            ]
        )

    @translate_assistant_errors
    async def get_conversation_state(
        self, assistant_id: str, conversation_id: str, state_id: str
    ) -> assistant_model.StateResponseModel:
        conversation_context = require_found(self.get_conversation_context(assistant_id, conversation_id))

        provider = self.assistant_app.inspector_state_providers.get(state_id)
        if provider is None:
            raise NotFoundError(f"inspector {state_id} not found")

        data = await provider.get(conversation_context)
        return assistant_model.StateResponseModel(
            id=state_id,
            data=data.data,
            json_schema=data.json_schema,
            ui_schema=data.ui_schema,
        )

    @translate_assistant_errors
    async def put_conversation_state(
        self,
        assistant_id: str,
        conversation_id: str,
        state_id: str,
        updated_state: assistant_model.StatePutRequestModel,
    ) -> assistant_model.StateResponseModel:
        conversation_context = require_found(self.get_conversation_context(assistant_id, conversation_id))

        provider = self.assistant_app.inspector_state_providers.get(state_id)
        if provider is None:
            raise NotFoundError(f"inspector {state_id} not found")

        if getattr(provider, "set", None) is None:
            raise BadRequestError(f"inspector {state_id} is read-only")

        await cast(WriteableAssistantConversationInspectorStateProvider, provider).set(
            conversation_context, updated_state.data
        )

        return await self.get_conversation_state(assistant_id, conversation_id, state_id)
