import asyncio
import logging
from dataclasses import dataclass, field
from typing import (
    IO,
    Any,
    AsyncContextManager,
    Awaitable,
    Callable,
    Generic,
    Mapping,
    Protocol,
    Sequence,
    TypeVar,
    Union,
)

from semantic_workbench_api_model import workbench_model

from .context import AssistantContext, ConversationContext

logger = logging.getLogger(__name__)


@dataclass
class AssistantConversationInspectorDataModel:
    data: dict[str, Any]
    json_schema: dict[str, Any] | None = field(default=None)
    ui_schema: dict[str, Any] | None = field(default=None)


class ReadOnlyAssistantConversationInspector(Protocol):
    display_name: str
    description: str

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorDataModel: ...


class WriteableAssistantConversationInspector(ReadOnlyAssistantConversationInspector):
    async def set(
        self,
        context: ConversationContext,
        data: dict[str, Any],
    ) -> None: ...


AssistantConversationInspector = Union[
    ReadOnlyAssistantConversationInspector,
    WriteableAssistantConversationInspector,
]


class AssistantContextExtender(Protocol):
    def extend(self, context: AssistantContext) -> Any: ...


class ConversationContextExtender(Protocol):
    def extend(self, context: ConversationContext) -> Any: ...


class AssistantDataExporter(Protocol):
    """
    Protocol to support the export and import of assistant-managed state.
    """

    def export(self, context: AssistantContext) -> AsyncContextManager[IO[bytes]]: ...

    async def import_(self, context: AssistantContext, stream: IO[bytes]) -> None: ...


class ConversationDataExporter(Protocol):
    """
    Protocol to support the export and import of assistant-managed-conversation state.
    """

    def export(self, context: ConversationContext) -> AsyncContextManager[IO[bytes]]: ...

    async def import_(self, context: ConversationContext, stream: IO[bytes]) -> None: ...


@dataclass
class AssistantConfigDataModel:
    config: dict[str, Any]
    json_schema: dict[str, Any] | None = field(default=None)
    ui_schema: dict[str, Any] | None = field(default=None)


class AssistantConfigProvider(Protocol):
    async def get(self, assistant_context: AssistantContext) -> AssistantConfigDataModel: ...

    async def set(self, assistant_context: AssistantContext, config: dict[str, Any]) -> None: ...


EventHandlerT = TypeVar("EventHandlerT")


class EventHandlerList(Generic[EventHandlerT], list[EventHandlerT]):

    async def __call__(self, *args, **kwargs):
        for handler in self:
            try:
                if asyncio.iscoroutinefunction(handler):
                    return await handler(*args, **kwargs)

                if callable(handler):
                    return handler(*args, **kwargs)

            except Exception:
                logger.exception("error in event handler {handler}")
                return

            raise TypeError(f"EventHandler {handler} is not a coroutine or callable")


class EventHandlers(Generic[EventHandlerT]):

    def __init__(self, on_created=True, on_updated=True, on_deleted=True) -> None:
        if on_created:
            self._on_created_handlers = EventHandlerList[EventHandlerT]()
            self.on_created = self._create_decorator(self._on_created_handlers)

        if on_updated:
            self._on_updated_handlers = EventHandlerList[EventHandlerT]()
            self.on_updated = self._create_decorator(self._on_updated_handlers)

        if on_deleted:
            self._on_deleted_handlers = EventHandlerList[EventHandlerT]()
            self.on_deleted = self._create_decorator(self._on_deleted_handlers)

    def _create_decorator(self, handler_list: list[EventHandlerT]) -> Callable[[EventHandlerT], EventHandlerT]:
        def decorator(func: EventHandlerT) -> EventHandlerT:
            handler_list.append(func)
            return func

        return decorator


AssistantEventHandler = Union[
    Callable[[AssistantContext], Awaitable[None]],
    Callable[[AssistantContext], None],
]

ConversationEventHandler = Union[
    Callable[[ConversationContext], Awaitable[None]],
    Callable[[ConversationContext], None],
]

ConversationParticipantEventHandler = Union[
    Callable[
        [ConversationContext, workbench_model.ConversationEvent, workbench_model.ConversationParticipant],
        Awaitable[None],
    ],
    Callable[[ConversationContext, workbench_model.ConversationEvent, workbench_model.ConversationParticipant], None],
]

ConversationMessageEventHandler = Union[
    Callable[
        [ConversationContext, workbench_model.ConversationEvent, workbench_model.ConversationMessage], Awaitable[None]
    ],
    Callable[[ConversationContext, workbench_model.ConversationEvent, workbench_model.ConversationMessage], None],
]

ConversationFileEventHandler = Union[
    Callable[
        [
            ConversationContext,
            workbench_model.ConversationEvent,
            workbench_model.File,
        ],
        Awaitable[None],
    ],
    Callable[
        [
            ConversationContext,
            workbench_model.ConversationEvent,
            workbench_model.File,
        ],
        None,
    ],
]


class MessageEvents(EventHandlers[ConversationMessageEventHandler]):
    def __init__(self) -> None:
        super().__init__(on_updated=False)

        self.chat = EventHandlers[ConversationMessageEventHandler](on_updated=False)
        self.log = EventHandlers[ConversationMessageEventHandler](on_updated=False)
        self.note = EventHandlers[ConversationMessageEventHandler](on_updated=False)
        self.notice = EventHandlers[ConversationMessageEventHandler](on_updated=False)
        self.command = EventHandlers[ConversationMessageEventHandler](on_updated=False)
        self.command_response = EventHandlers[ConversationMessageEventHandler](on_updated=False)
        # ensure we have an event handler for each message type
        for event_type in workbench_model.MessageType:
            assert getattr(self, str(event_type).replace("-", "_"))


class ConversationEvents(EventHandlers[ConversationEventHandler]):

    def __init__(self) -> None:
        super().__init__()

        self.participant = EventHandlers[ConversationParticipantEventHandler](on_deleted=False)
        self.file = EventHandlers[ConversationFileEventHandler]()
        self.message = MessageEvents()


class Events:

    def __init__(self) -> None:
        self.assistant = EventHandlers[AssistantEventHandler]()
        self.conversation = ConversationEvents()


class ContentInterceptor(Protocol):
    """
    Protocol to support the interception of incoming and outgoing messages.

    **Properties**
    - **metadata_key(str)**
        - Intended to be used to store evaluation results and other metadata related to the
            interceptor actions taken and may be used elsewhere to access the data. This key
            should be unique to the interceptor.

    **Methods**
    - **intercept_incoming_event(context, event) -> ConversationEvent | None**
        - Intercept incoming events before they are processed by the assistant.
    - **intercept_outgoing_messages(context, messages) -> list[NewConversationMessage]**
        - Intercept outgoing messages before they are sent to the conversation.
    """

    @property
    def metadata_key(self) -> str: ...

    async def intercept_incoming_event(
        self, context: ConversationContext, event: workbench_model.ConversationEvent
    ) -> workbench_model.ConversationEvent | None: ...

    async def intercept_outgoing_messages(
        self, context: ConversationContext, messages: list[workbench_model.NewConversationMessage]
    ) -> list[workbench_model.NewConversationMessage]: ...


class AssistantAppProtocol(Protocol):
    _assistant_service_id: str
    _assistant_service_name: str
    _assistant_service_description: str

    _config_provider: AssistantConfigProvider
    _data_exporter: AssistantDataExporter
    _conversation_data_exporter: ConversationDataExporter

    context_extenders: Sequence[AssistantContextExtender]
    conversation_context_extenders: Sequence[ConversationContextExtender]
    events: Events
    inspectors: Mapping[str, AssistantConversationInspector]
    content_interceptor: ContentInterceptor | None
