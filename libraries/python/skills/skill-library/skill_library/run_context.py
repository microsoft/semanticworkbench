import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Awaitable, Callable, Concatenate, ParamSpec, Protocol
from uuid import uuid4

from assistant_drive import Drive
from events.events import EventProtocol

from .routine_stack import RoutineStack


class LogEmitter:
    """A simple event emitter that logs the event to the console. This will be
    what is used unless a different emitter is provided."""

    def emit(self, event: EventProtocol) -> None:
        logging.info(event.to_json())


async def unimplemented_routine_runner(routine_name: str, *args: Any, **kwargs: Any) -> None:
    """A runner that logs a message when a routine has not been implemented."""
    logging.info("Routine runner has not been implemented.")


async def unimplemented_action_runner(action_name: str, *args: Any, **kwargs: Any) -> None:
    """A runner that logs a message when a routine has not been implemented."""
    logging.info("Action runner has not been implemented.")


# A typing spec for *args, **kwargs, used in run_action and run_routine sigs.
P = ParamSpec("P")


class RunContext:
    """
    "Run context" is passed to parts of the system (skill routines and
    actions, and chat driver functions) that need to be able to run routines or
    actions, set assistant state, or emit messages from the assistant.
    """

    def __init__(
        self,
        session_id: str,
        assistant_drive: Drive,
        emit: Callable[[EventProtocol], None],
        routine_stack: RoutineStack,
        run_action: Callable[Concatenate[str, P], Awaitable[Any]],
        run_routine: Callable[Concatenate[str, P], Awaitable[Any]],
    ) -> None:
        # A session id is useful for maintaining consistent session state across all
        # consumers of this context. For example, a session id can be set in an
        # assistant and all functions called by that assistant can should receive
        # this same context object to know which session is being used.
        self.session_id: str = session_id or str(uuid4())

        # The assistant drive is a drive object that can be used to read and
        # write files to a particular location. The assistant drive should be
        # used for assistant-specific data and not for general data storage.
        self.assistant_drive: Drive = assistant_drive

        # A "run" is a particular series of calls within a session. The initial call will
        # set the run id and all subsequent calls will use the same run id. This is useful
        # for logging, metrics, and debugging.
        self.run_id: str | None = str(uuid4())

        # The emit function is used to send events to the event bus. The component
        # that creates this context object will be responsible for instantiating an
        # event bus and handling the events sent to it with this function.
        self.emit = emit or LogEmitter().emit

        self.run_routine = run_routine or unimplemented_routine_runner
        self.run_action = run_action or unimplemented_action_runner

        # Helper functions for managing state of the current routine being run.
        self.get_state = routine_stack.get_current_state
        self.get_state_key = routine_stack.get_current_state_key
        self.set_state = routine_stack.set_current_state
        self.set_state_key = routine_stack.set_current_state_key

    @asynccontextmanager
    async def stack_frame_state(self) -> AsyncGenerator[dict[str, Any], None]:
        """
        A context manager that allows you to get and set the state of the
        current routine being run. This is useful for storing and retrieving
        information that is needed across multiple steps of a routine.

        Example:

        ```
        async with context.stack_frame_state() as state:
            state["key"] = "value"
        ```
        """
        state = await self.get_state()
        yield state
        await self.set_state(state)


class RunContextProvider(Protocol):
    """
    A provider of a run context must have this method. When called, it will
    return a run context. This is used by skill routines and actions to have
    access to all the things they need for running.
    """

    def create_run_context(self) -> RunContext: ...
