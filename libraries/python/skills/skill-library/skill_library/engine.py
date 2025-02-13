# skill_library/engine.py

import asyncio
import traceback
from os import PathLike
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Type,
)
from uuid import uuid4

from assistant_drive import Drive, DriveConfig, IfDriveFileExistsBehavior
from events import EventProtocol, InformationEvent, MessageEvent, StatusUpdatedEvent
from semantic_workbench_api_model.workbench_model import ConversationMessageList

from .logging import extra_data, logger
from .routine_stack import RoutineStack
from .skill import Skill, SkillConfig
from .types import RunContext


class Engine:
    """
    Main coordination point for skills, routines and user interaction.

    The Engine manages the execution of routines and actions from skills that
    are available to the system. Skills are registered with configurations on
    initialization. When a routine is run, the Engine:

    1. Creates a task to execute the routine asynchronously
    2. Manages user interaction by:
        - Having routines use ask_user() to request input
        - Handling resumption of routines when input arrives
    3. Tracks state through:
        - The routine stack for nested routine calls
        - The routine stack tuple containing (result_future, input_future) for
          the active routine
        - State storage for routines to persist data between steps

    The core interaction pattern is:

    - Engine.run_routine() starts a routine that can request user input via
      ask_user()
    - When ask_user() is called, the routine pauses until
      Engine.resume_routine() is called - When user input arrives,
      resume_routine() allows the routine to continue executing
    - This cycle repeats until the routine completes

    This async interaction pattern allows routines to have natural dialogue
    flows while keeping the overall system responsive.
    """

    def __init__(
        self,
        engine_id: str | None,
        message_history_provider: Callable[[], Awaitable[ConversationMessageList]],
        skills: list[tuple[Type[Skill], SkillConfig]] | None = None,
        drive_root: PathLike | None = None,
        metadata_drive_root: PathLike | None = None,
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
                self._skills[config.name] = skill_class(config)

        self._routine_stack: list[asyncio.Future] = []
        self._current_input_future: asyncio.Future | None = None

        logger.debug("Skill engine initialized.", extra_data({"engine_id": self.engine_id}))

    async def clear(self, include_drives: bool = True) -> None:
        """Clears the engine's routine stack and event queue."""
        await self.routine_stack.clear()
        while not self._event_queue.empty():
            self._event_queue.get_nowait()
        if include_drives:
            self.metadrive.delete_drive()
            self.drive.delete_drive()

        logger.debug("Skill engine state cleared.", extra_data({"engine_id": self.engine_id}))

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
            "Engine queud an event (_emit).", extra_data({"event": {"id": event.id, "message": event.message}})
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
            skills=self._skills,
        )

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
            self._emit(InformationEvent(message=f"Action {action_name} not found in skill {skill_name}"))
            # raise ValueError(f"Action {action_name} not found in skill {skill_name}")
            return

        try:
            result = await action(self.create_run_context(), *args, **kwargs)
            result_hint = f"{str(result)[:200]}..." if len(str(result)) > 200 else str(result)
            self._emit(InformationEvent(message=f"Executed action {designation} with result: {result_hint}"))
            return result
        except Exception as e:
            tb = traceback.format_exc()
            self._emit(InformationEvent(message=f"Error in action {designation}: {str(e)}\n{tb}"))
            return
        # return await action(self.create_run_context(), *args, **kwargs)

    def list_routines(self) -> list[str]:
        """List all available routines in format skill_name.routine_name"""
        routines = []
        for skill_name, skill in self._skills.items():
            routines.extend(f"{skill_name}.{routine}" for routine in skill.list_routines())
        return routines

    ######################################
    # Routine running and resumption.
    ######################################

    def is_routine_running(self) -> bool:
        return self._current_input_future is not None

    async def _run_routine_task(
        self,
        designation: str,
        routine,
        result_future: asyncio.Future,
        *args: Any,
        **kwargs: Any,
    ):
        try:
            logger.debug(
                "Starting routine task.",
                extra_data({"designation": designation, "stack": [id(rf) for rf in self._routine_stack]}),
            )
            self._emit(StatusUpdatedEvent(message=f"Executing routine: {designation}"))
            context = self.create_run_context()

            async def ask_user(prompt: str) -> str:
                self._emit(MessageEvent(message=prompt))
                self._emit(StatusUpdatedEvent())
                logger.debug("Routine paused for ask_user.", extra_data({"prompt": prompt}))

                # Create new input future
                self._current_input_future = asyncio.Future()
                return await self._current_input_future

            async def print(message: str) -> None:
                self._emit(InformationEvent(message=message))

            # Run the routine, but await
            result = await routine(
                context,
                ask_user,
                print,
                self.run_action,
                self.run_routine,
                self.routine_stack.get_current_state,
                self.routine_stack.set_current_state,
                self._emit,
                *args,
                **kwargs,
            )

            # When the routine completes, set the result on the result future.
            logger.debug(f"Routine {designation} executed successfully. Result: {result}")
            result_future.set_result(result)
            self._emit(InformationEvent(message=str(result)))

        except Exception as e:
            tb = traceback.format_exc()
            self._emit(InformationEvent(message=f"Error in routine {designation}: {str(e)}\n{tb}"))
            result_future.set_exception(e)
        finally:
            if self._routine_stack:
                popped = self._routine_stack.pop()
                logger.debug("Popped result future.", extra_data({"id": id(popped)}))
            self._emit(StatusUpdatedEvent())
            await self.routine_stack.pop()

    async def run_routine(self, designation: str, *args: Any, **kwargs: Any) -> Any:
        """
        Run a routine and return its result. This blocks until the routine
        completes, but the Engine remains responsive to input via
        resume_routine.
        """
        skill_name, routine_name = designation.split(".")
        skill = self._skills[skill_name]
        routine = skill.get_routine(routine_name)
        if not routine:
            self._emit(InformationEvent(message=f"Routine {designation} not found"))
            # raise ValueError(f"Routine {designation} not found")
            return

        result_future = asyncio.Future()
        logger.debug("Creating new routine.", extra_data({"designation": designation, "id": id(result_future)}))
        self._routine_stack.append(result_future)

        # Create task but don't await it yet
        asyncio.create_task(self._run_routine_task(designation, routine, result_future, *args, **kwargs))

        # Return the result future directly
        return await result_future

    async def resume_routine(self, message: str) -> None:
        logger.debug("Resume routine called.", extra_data({"message": message}))
        if self._current_input_future:
            logger.debug("Setting result for input_future.", extra_data({"id": id(self._current_input_future)}))
            self._current_input_future.set_result(message)
            self._current_input_future = None
        else:
            logger.debug("No current routine to resume")
