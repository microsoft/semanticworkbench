import logging
from os import PathLike
from typing import Any, Callable, Coroutine, Optional
from uuid import uuid4

from assistant_drive import Drive, DriveConfig, IfDriveFileExistsBehavior
from context import ContextProtocol
from events.events import EventProtocol

from .routine_stack import RoutineStack


class LogEmitter:
    """A simple event emitter that logs the event to the console. This will be
    what is used unless a different emitter is provided."""

    def emit(self, event: EventProtocol) -> None:
        logging.info(event.to_json())


class RunContext(ContextProtocol):
    def __init__(
        self,
        session_id: str,
        assistant_drive: Drive,
        emit: Callable[[EventProtocol], None],
        run_routine: Callable[["RunContext", str, Optional[dict[str, Any]]], Coroutine[Any, Any, Any]],
        metadata_drive_root: PathLike | None = None,
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
        self.run_id: str = str(uuid4())

        # The emit function is used to send events to the event bus. The component
        # that creates this context object will be responsible for instantiating an
        # event bus and handling the events sent to it with this function.
        self.emit = emit or LogEmitter().emit

        # A metadrive to be used for managing assistant metadata. This can be
        # useful for storing session data, logs, and other information that
        # needs to be persisted across different calls to the assistant.
        self.metadrive: Drive = Drive(
            DriveConfig(
                root=metadata_drive_root or f".data/{session_id}/.assistant",
                default_if_exists_behavior=IfDriveFileExistsBehavior.OVERWRITE,
            )
        )

        # Functions for running routines.
        self.run_routine = run_routine

        # The routine stack is used to keep track of the current routine being
        # run by the assistant.
        self.routine_stack: RoutineStack = RoutineStack(self.metadrive)

        # Helper functions for managing state of the current routine being run.
        self.state = self.routine_stack.get_current_state
        self.state_key = self.routine_stack.get_current_state_key
        self.update_state = self.routine_stack.set_current_state
        self.update_state_key = self.routine_stack.set_current_state_key
