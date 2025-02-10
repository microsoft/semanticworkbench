import asyncio
from os import PathLike
from typing import Any, AsyncIterator, Awaitable, Callable, Type
from uuid import uuid4

from assistant_drive import Drive, DriveConfig, IfDriveFileExistsBehavior
from events import EventProtocol
from semantic_workbench_api_model.workbench_model import ConversationMessageList

from skill_library.logging import extra_data, logger

from .routine_runner import RoutineRunner
from .routine_stack import RoutineStack
from .run_context import RunContext
from .skill import Skill, SkillConfig


class Engine:
    def __init__(
        self,
        name,
        engine_id: str | None,
        message_history_provider: Callable[[], Awaitable[ConversationMessageList]],
        drive_root: PathLike | None = None,
        metadata_drive_root: PathLike | None = None,
        skills: list[tuple[Type[Skill], SkillConfig]] | None = None,
    ) -> None:
        # This, though, we use.
        self.engine_id = engine_id or str(uuid4())

        # A metadrive to be used for managing assistant metadata. This can be
        # useful for storing session data, logs, and other information that
        # needs to be persisted across different calls to the assistant. This is
        # not data intended to be accessed by users or skills.
        self.metadrive = Drive(
            DriveConfig(
                root=metadata_drive_root or f".data/{engine_id}/.assistant",
                default_if_exists_behavior=IfDriveFileExistsBehavior.OVERWRITE,
            )
        )

        # The routine stack is used to keep track of the current routine being
        # run by the assistant.
        self.routine_stack = RoutineStack(self.metadrive)

        # Set up the assistant event queue.
        self._event_queue = asyncio.Queue()  # Async queue for events
        self._stopped = asyncio.Event()  # Event to signal when the assistant has stopped

        # The assistant drive is used as the storage bucket for all assistant
        # and skill data. Skills will generally create a subdrive off of this
        # drive.
        self.drive = Drive(
            DriveConfig(
                root=drive_root or f".data/{engine_id}/assistant",
                default_if_exists_behavior=IfDriveFileExistsBehavior.OVERWRITE,
            )
        )

        self.message_history_provider = message_history_provider

        # Initialize skills with their configs
        self._skills: dict[str, Skill] = {}
        if skills:
            for skill_class, config in skills:
                self._skills[config.skill_name] = skill_class(config)

    async def clear(self, include_drives: bool = True) -> None:
        """Clears the assistant's routine stack and event queue."""
        await self.routine_stack.clear()
        while not self._event_queue.empty():
            self._event_queue.get_nowait()
        if include_drives:
            self.metadrive.delete_drive()
            self.drive.delete_drive()

    ######################################
    # Lifecycle and event handling
    ######################################

    async def start(self) -> None:
        """Start the assistant."""
        self._stopped.clear()

    async def wait(self) -> str:
        """
        After initializing an assistant, call this method to wait for assistant
        events. While running, any events produced by the assistant can be
        accessed through the `events` property. When the assistant completes,
        this method returns the assistant_id of the assistant.
        """
        await self._stopped.wait()
        return self.engine_id

    def stop(self) -> None:
        self._stopped.set()  # Signal that we are stopping

    @property
    async def events(self) -> AsyncIterator[EventProtocol]:
        """
        This method is a generator that yields events produced by the assistant
        as they are emitted. The generator will continue to yield events until
        the assistant has completed AND all events have been emitted.
        """
        logger.debug("Assistant started. Listening for events.")
        while not self._stopped.is_set():
            try:
                # async with asyncio.timeout(1):
                yield await self._event_queue.get()
            except asyncio.TimeoutError:
                continue
        logger.debug("Assistant stopped. No more events will be emitted.")

    def _emit(self, event: EventProtocol) -> None:
        event.session_id = self.engine_id
        self._event_queue.put_nowait(event)
        logger.debug(
            "Assistant queud an event (_emit).", extra_data({"event": {"id": event.id, "message": event.message}})
        )

    def create_run_context(self) -> RunContext:
        # The run context is passed to parts of the system (skill routines and
        # actions, and chat driver functions) that need to be able to run
        # routines or actions, set assistant state, or emit messages from the
        # assistant.

        return RunContext(
            session_id=self.engine_id,
            assistant_drive=self.drive,
            conversation_history=self.message_history_provider,
            emit=self._emit,
            run_action=self.run_action,
            run_routine=self.run_routine,
            get_state=self.routine_stack.get_current_state,
            set_state=self.routine_stack.set_current_state,
            skills=self._skills,
        )

    def list_routines(self) -> list[str]:
        """List all available routines in format skill_name.routine_name"""
        routines = []
        for skill_name, skill in self._skills.items():
            routines.extend(f"{skill_name}.{routine}" for routine in skill.list_routines())
        return routines

    async def run_routine(self, designation: str, *args: Any, **kwargs: Any) -> Any:
        """Run a routine like 'posix.create_file_interactive'"""
        skill_name, routine_name = designation.split(".")
        if skill_name not in self._skills:
            raise ValueError(f"Skill {skill_name} not found")

        skill = self._skills[skill_name]
        routine = skill.get_routine(routine_name)
        if not routine:
            raise ValueError(f"Routine {routine_name} not found in skill {skill_name}")

        self.current_run = RoutineRunner(self.routine_stack)
        return await self.current_run.start(self.create_run_context(), routine, *args, **kwargs)

    async def resume_routine(self, message: str) -> None:
        if self.current_run:
            self.current_run.resume(message)

    def list_actions(self) -> list[str]:
        """List all available actions in format skill_name.action_name"""
        actions = []
        for skill_name, skill in self._skills.items():
            actions.extend(f"{skill_name}.{action}" for action in skill.list_actions())
        return actions

    async def run_action(self, designation: str, *args: Any, **kwargs: Any) -> Any:
        """
        Run an assistant action by name (e.g. <skill_name>.<action_name>).
        """
        skill_name, action_name = designation.split(".")
        if skill_name not in self._skills:
            raise ValueError(f"Skill {skill_name} not found")

        skill = self._skills[skill_name]
        action = skill.get_action(action_name)
        if not action:
            raise ValueError(f"Action {action_name} not found in skill {skill_name}")

        return await action(self.create_run_context())
