import logging
from typing import Any, Callable, Optional, Protocol, runtime_checkable
from uuid import uuid4

from events.events import EventProtocol


@runtime_checkable
class ContextProtocol(Protocol):
    """A protocol for the context object that is passed to all components
    (functions, action, routines, etc.). The context object is used to pass
    information between these components, such as the session_id and
    run_id. The context object also carries the function used by actions and
    routines to emit events."""

    # A session id is useful for maintaining consistent session state across all
    # consumers of this context. For example, a session id can be set in an
    # assistant and all functions called by that assistant can should receive
    # this same context object to know which session is being used.
    session_id: str

    # A "run" is a particular series of calls within a session. The initial call will
    # set the run id and all subsequent calls will use the same run id. This is useful
    # for logging, metrics, and debugging.
    run_id: Optional[str]

    # The emit function is used to send events to the event bus. The component
    # that creates this context object will be responsible for instantiating an
    # event bus and handling the events sent to it with this function.
    emit: Callable[[EventProtocol], None]


class LogEmitter:
    """A simple event emitter that logs the event to the console. This will be
    what is used unless a different emitter is provided."""

    def emit(self, event: EventProtocol) -> None:
        logging.info(event.to_json())


class Context(ContextProtocol):
    """A default context object that implements the ContextProtocol. The context
    object that is passed to all components (functions, action, routines, etc.).
    The context object is used to pass information between these components,
    such as the session_id and run_id. The context object also carries the
    function used by actions and routines to emit events."""

    def __init__(
        self,
        session_id: str | None = None,
        run_id: str | None = None,
        emit: Optional[Callable[[EventProtocol], None]] = None,
    ) -> None:
        self.session_id = session_id or str(uuid4())
        self.run_id = run_id
        self.emit = emit or LogEmitter().emit

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "run_id": self.run_id,
            "emit": self.emit.__class__.__name__,
        }

    def __repr__(self) -> str:
        return f"Context({self.session_id})"

    def __str__(self) -> str:
        return f"Context({self.session_id})"
