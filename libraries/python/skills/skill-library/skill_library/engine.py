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
from events import ErrorEvent, EventProtocol, InformationEvent, MessageEvent, StatusUpdatedEvent
from semantic_workbench_api_model.workbench_model import ConversationMessageList

from .logging import extra_data, logger
from .routine_stack import RoutineStack
from .skill import Skill, SkillConfig
from .types import RunContext
from .usage import routines_usage as usage_routines_usage


class Engine:
    """
    Main coordination point for skills, routines and user interaction.

    The Engine manages the execution of routines from skills that are registered
    to it. Skills are registered with configurations on initialization. When a
    routine is run, the Engine:

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

        # The routine stack is used to keep state isolated between nested
        # routines. Each routine gets a frame on the stack that contains its
        # state. When a routine calls another routine, the new routine gets a
        # new frame on the stack. When the new routine completes, its frame is
        # popped off the stack and the original routine can continue.
        self.routine_stack = RoutineStack(self.metadrive)

        # Set up the engine event queue.
        self._event_queue = asyncio.Queue()  # Async queue for events
        self._stopped = asyncio.Event()  # Event to signal when the engine has stopped

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

        self._routine_output_futures: list[asyncio.Future] = []
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
        self._emit(StatusUpdatedEvent())

        logger.debug("Skill engine state cleared.", extra_data({"engine_id": self.engine_id}))

    ######################################
    # Lifecycle and event handling
    ######################################

    async def start(self) -> None:
        """Start the engine."""
        self._stopped.clear()

    async def wait(self) -> str:
        """
        After initializing an engine, call this method to wait for engine
        events. While running, any events produced by the engine can be
        accessed through the `events` property. When the engine completes,
        this method returns the engine_id of the engine.
        """
        await self._stopped.wait()
        return self.engine_id

    def stop(self) -> None:
        self._stopped.set()  # Signal that we are stopping

    @property
    async def events(self) -> AsyncIterator[EventProtocol]:
        """
        This method is a generator that yields events produced by the engine
        as they are emitted. The generator will continue to yield events until
        the engine has completed AND all events have been emitted.
        """
        logger.debug("Assistant started. Listening for events.")
        while not self._stopped.is_set():
            try:
                yield await self._event_queue.get()
            except asyncio.TimeoutError:
                continue
        logger.debug("Assistant stopped. No more events will be emitted.")

    def _emit(self, event: EventProtocol) -> None:
        event.session_id = self.engine_id
        self._event_queue.put_nowait(event)
        logger.debug(
            "Engine queued an event (_emit).", extra_data({"event": {"id": event.id, "message": event.message}})
        )

    ######################################
    # Routine running and resumption.
    ######################################

    def list_routines(self) -> list[str]:
        """List all available routines in format skill_name.routine_name"""
        routines = []
        for skill_name, skill in self._skills.items():
            routines.extend(f"{skill_name}.{routine}" for routine in skill.list_routines())
        return routines

    def routines_usage(self) -> str:
        """Get a list of all routines and their usage."""
        return usage_routines_usage(self._skills)

    def is_routine_running(self) -> bool:
        return self._current_input_future is not None

    async def _run_routine_task(
        self,
        run_context: RunContext,
        designation: str,
        routine,
        result_future: asyncio.Future,
        *args: Any,
        **kwargs: Any,
    ):
        try:
            logger.debug(
                "Starting routine task.",
                extra_data({"designation": designation, "stack": [id(rf) for rf in self._routine_output_futures]}),
            )
            self._emit(StatusUpdatedEvent(message=f"Executing routine: {designation}"))

            async def ask_user(prompt: str) -> str:
                self._emit(MessageEvent(message=prompt))
                self._emit(StatusUpdatedEvent())
                logger.debug("Routine paused for ask_user.", extra_data({"prompt": prompt}))

                # Create new input future
                self._current_input_future = asyncio.Future()
                return await self._current_input_future

            async def run_routine_context_wrapper(designation: str, *args: Any, **kwargs: Any) -> Any:
                return await self.run_routine_with_context(run_context, designation, *args, **kwargs)

            # Run the routine, but await
            routine_stack_state = await self.routine_stack.get_current_state()
            result = await routine(
                run_context,
                routine_stack_state,
                self._emit,
                run_routine_context_wrapper,
                ask_user,
                *args,
                **kwargs,
            )
            await self.routine_stack.set_current_state(routine_stack_state)

            # When the routine completes, set the result on the result future.
            logger.debug(f"Routine {designation} executed successfully. Result: {result}")
            result_future.set_result(result)
            # self._emit(InformationEvent(message=f"Routine `{designation}` completed successfully. Result: {result}"))

        except Exception as e:
            result_future.set_exception(e)
        finally:
            if self._routine_output_futures:
                popped = self._routine_output_futures.pop()
                logger.debug("Popped result future.", extra_data({"id": id(popped)}))
            self._emit(StatusUpdatedEvent())
            await self.routine_stack.pop()

    async def run_routine(self, designation: str, *args: Any, **kwargs: Any) -> Any:
        """
        Start a new run with an initial routine. This is the entrypoint from
        outside the engine. All internal calls (a subroutine for a routine) will
        be calling `run_routine_with_context` so the same `run_id` will be used
        throughout the routine run.
        """

        run_context = RunContext(
            session_id=self.engine_id,
            run_drive=self.drive,
            conversation_history=self.message_history_provider,
            skills=self._skills,
        )

        try:
            result = await self.run_routine_with_context(run_context, designation, *args, **kwargs)
            self._emit(InformationEvent(message=str(result), metadata=run_context.flattened_metadata()))
        except Exception as e:
            tb = traceback.format_exc()
            self._emit(
                ErrorEvent(
                    message=f"Error in routine `{designation}`:\n\n```{str(e)}\n\n{tb}```",
                    metadata=run_context.flattened_metadata(),
                )
            )
            raise e

        return result

    async def run_routine_with_context(
        self, run_context: RunContext, designation: str, *args: Any, **kwargs: Any
    ) -> Any:
        """
        Run a routine and return its result. This blocks until the routine
        completes, but the Engine remains responsive to input via
        resume_routine.
        """
        skill_name, routine_name = designation.split(".")
        skill = self._skills[skill_name]
        routine = skill.get_routine(routine_name)
        if not routine:
            run_context.log("Engine error", {"message": f"Routine {designation} not found"})
            return

        result_future = asyncio.Future()
        logger.debug("Creating new routine.", extra_data({"designation": designation, "id": id(result_future)}))
        self._routine_output_futures.append(result_future)

        # Create task but don't await it yet.
        asyncio.create_task(self._run_routine_task(run_context, designation, routine, result_future, *args, **kwargs))

        # Return the result future directly.
        return await result_future

    async def resume_routine(self, message: str) -> None:
        logger.debug("Resume routine called.", extra_data({"message": message}))
        if self._current_input_future:
            logger.debug("Setting result for input_future.", extra_data({"id": id(self._current_input_future)}))
            self._current_input_future.set_result(message)
            self._current_input_future = None
        else:
            logger.debug("No current routine to resume")
