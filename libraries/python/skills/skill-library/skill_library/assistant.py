import asyncio
from os import PathLike
from typing import Any, AsyncIterator, Callable, Optional
from uuid import uuid4

from assistant_drive import Drive, DriveConfig, IfDriveFileExistsBehavior
from events import BaseEvent, EventProtocol
from openai.types.chat.completion_create_params import (
    ResponseFormat,
)
from openai_client.chat_driver import (
    ChatDriver,
    ChatDriverConfig,
    LocalMessageHistoryProvider,
    LocalMessageHistoryProviderConfig,
)
from openai_client.completion import TEXT_RESPONSE_FORMAT
from openai_client.messages import format_with_liquid

from skill_library.routine_stack import RoutineStack

from .logging import extra_data, logger
from .run_context import RunContext
from .skill import SkillDefinition
from .skill_registry import SkillRegistry
from .types import Metadata


class Assistant:
    def __init__(
        self,
        name,
        assistant_id: str | None,
        chat_driver_config: ChatDriverConfig,
        drive_root: PathLike | None = None,
        metadata_drive_root: PathLike | None = None,
        skills: dict[str, SkillDefinition] | None = None,
        startup_action: str | None = None,
        startup_routine: str | None = None,
        startup_args: tuple = (),
        startup_kwargs: dict[str, Any] = {},
    ) -> None:
        # Do we ever use this? No. We don't. It just seems like it would be a
        # good idea, though.
        self.name = name

        # This, though, we use.
        self.assistant_id = assistant_id or str(uuid4())

        # A metadrive to be used for managing assistant metadata. This can be
        # useful for storing session data, logs, and other information that
        # needs to be persisted across different calls to the assistant. This is
        # not data intended to be accessed by users or skills.
        self.metadrive = Drive(
            DriveConfig(
                root=metadata_drive_root or f".data/{assistant_id}/.assistant",
                default_if_exists_behavior=IfDriveFileExistsBehavior.OVERWRITE,
            )
        )

        # The routine stack is used to keep track of the current routine being
        # run by the assistant.
        self.routine_stack = RoutineStack(self.metadrive)

        # Register all skills for the assistant.
        self.skill_registry = SkillRegistry(skills, self, self.routine_stack) if skills else None

        # Set up the assistant event queue.
        self._event_queue = asyncio.Queue()  # Async queue for events
        self._stopped = asyncio.Event()  # Event to signal when the assistant has stopped

        # The assistant drive is used as the storage bucket for all assistant
        # and skill data. Skills will generally create a subdrive off of this
        # drive.
        self.drive = Drive(
            DriveConfig(
                root=drive_root or f".data/{assistant_id}/assistant",
                default_if_exists_behavior=IfDriveFileExistsBehavior.OVERWRITE,
            )
        )

        # Configure the assistant chat interface.
        self.chat_driver = self._register_chat_driver(chat_driver_config)

        self.startup_action = startup_action
        self.startup_routine = startup_routine
        self.startup_args = startup_args
        self.startup_kwargs = startup_kwargs

    async def clear(self) -> None:
        """Clears the assistant's routine stack and event queue."""
        await self.routine_stack.clear()
        while not self._event_queue.empty():
            self._event_queue.get_nowait()
        self.metadrive.delete()
        self.drive.delete()

    ######################################
    # Lifecycle and event handling
    ######################################

    async def start(self) -> None:
        """Start the assistant."""
        self._stopped.clear()

        # If a startup action is provided, run it.
        if self.startup_action:
            await self.run_action(self.startup_action, *self.startup_args, **self.startup_kwargs)

        # If a startup routine is provided, run it.
        if self.startup_routine:
            await self.run_routine(self.startup_routine, *self.startup_args, **self.startup_kwargs)

    async def wait(self) -> str:
        """
        After initializing an assistant, call this method to wait for assistant
        events. While running, any events produced by the assistant can be
        accessed through the `events` property. When the assistant completes,
        this method returns the assistant_id of the assistant.
        """
        await self._stopped.wait()
        return self.assistant_id

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
        event.session_id = self.assistant_id
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
            session_id=self.assistant_id,
            assistant_drive=self.drive,
            emit=self._emit,
            run_action=self.run_action,
            run_routine=self.run_routine,
            routine_stack=self.routine_stack,
        )

    async def put_message(self, message: str, metadata: Optional[Metadata] = None) -> None:
        """
        Exposed externally for sending messages to the assistant.

        If a routine is currently running, send the message to the routine.

        This is a simple way to handle conversation flows. In the future, we
        would like to keep track of multiple topics and allow the assistant to
        switch between them. The current idea is that we might treat a topic
        like multi-tasking on a Linux system with one topic at a time being
        "foreground" and the others being "background". The assistant would
        decide when to switch topics based on the content of the messages. A
        topic might include a subset of the conversation history, only specific
        skills, etc.

        For now, though, we track only a single topic at a time. If a routine is
        currently running, we send the message to the routine. Otherwise, we
        send the message to the chat driver.
        """
        # If a routine is running, send the message to the routine.
        if await self.routine_stack.peek():
            await self.step_active_routine(message)
        else:
            # Otherwise, send the message to the chat driver.
            response = await self.chat_driver.respond(message, metadata=metadata)
            self._emit(response)

    ######################################
    # Chat interface
    ######################################

    def _register_chat_driver(self, chat_driver_config: ChatDriverConfig) -> ChatDriver:
        """Sets up a chat driver for the assistant."""
        config = ChatDriverConfig(**dict(chat_driver_config.__dict__))
        config.instructions = (
            f"{config.instructions}"
            "\n\nYou have the ability to run functions and routines.\n\n"
            "Run a routine with the run_routine function passing it the name of the routine "
            "and arguments."
            "Available routines: {routines}. "
        )
        if chat_driver_config.message_provider is None:
            chat_driver_config.message_provider = LocalMessageHistoryProvider(
                LocalMessageHistoryProviderConfig(session_id=self.assistant_id, formatter=format_with_liquid)
            )
        chat_functions = ChatFunctions(self)
        config.commands = chat_functions.list_functions()
        config.functions = [chat_functions.list_actions, chat_functions.list_routines]
        return ChatDriver(config)

    async def generate_response(
        self,
        message: str,
        response_format: ResponseFormat = TEXT_RESPONSE_FORMAT,
        instruction_parameters: dict[str, Any] = {},
    ) -> BaseEvent:
        """
        Generate a response to a user message. This method is exposed externally
        as a simple way to interact with the assistant. Typically, though, you
        would interact with the assistant by sending messages to it through the
        `put_message` method and handling responses through the `events`.
        """
        if not self.chat_driver:
            raise ValueError("No chat driver registered for this assistant.")

        if self.skill_registry:
            instruction_parameters["actions"] = ", ".join(self.skill_registry.list_actions())
            instruction_parameters["routines"] = ", ".join(self.skill_registry.list_routines())

        return await self.chat_driver.respond(
            message,
            response_format=response_format,
            instruction_parameters=instruction_parameters,
        )

    ######################################
    # Skill interface
    ######################################

    def list_routines(self) -> list[str]:
        """Lists all the routines the assistant is able to perform."""
        return self.skill_registry.list_routines() if self.skill_registry else []

    async def run_routine(self, name: str, *args, **kwargs) -> Any:
        """
        Run an assistant routine by name (e.g. <skill_name>.<routine_name>).
        """
        if not self.skill_registry:
            raise ValueError("No skill registry registered for this assistant.")
        await self.skill_registry.run_routine_by_designation(self.create_run_context(), name, *args, **kwargs)

    def list_actions(self) -> list[str]:
        """Lists all the actions the assistant is able to perform."""
        return self.skill_registry.list_actions() if self.skill_registry else []

    def run_action(self, designation: str, *args, **kwargs) -> Any:
        """
        Run an assistant action by name (e.g. <skill_name>.<action_name>).
        """
        if not self.skill_registry:
            raise ValueError("No skill registry registered for this assistant.")
        return self.skill_registry.run_action_by_designation(self.create_run_context(), designation, *args, **kwargs)

    async def step_active_routine(self, message: str) -> None:
        """Run another step in the current routine."""
        if not self.skill_registry:
            raise ValueError("No skill registry registered for this assistant.")
        await self.skill_registry.step_active_routine(self.create_run_context(), message)


class ChatFunctions:
    """
    These functions provide usage context and output markdown. It's a layer
    closer to the assistant.
    """

    def __init__(self, assistant: Assistant) -> None:
        self.assistant = assistant

    def list_routines(self) -> str:
        """Lists all the routines available in the assistant."""
        if not self.assistant.skill_registry:
            return "No routines available."

        routines = []
        for skill_name, skill in self.assistant.skill_registry.skills.items():
            for routine in skill.get_routines():
                routines.append(f"- __{skill_name}.{routine.name}__: _{routine.description}_")

        if not routines:
            return "No routines available."

        routine_string = "```markdown\n### Routines\n\n" + "\n".join(routines) + "\n```"
        # self.assistant._emit(InformationEvent(message=routine_string))
        return routine_string

    async def run_routine(self, name: str, *args, **kwargs) -> Any:
        """
        Run an assistant routine.
        """
        await self.assistant.run_routine(name, *args, **kwargs)

    def list_actions(self) -> str:
        """Lists all the actions available in the assistant."""
        if not self.assistant.skill_registry:
            return "No actions available."

        actions = []
        for skill_name, skill in self.assistant.skill_registry.skills.items():
            for action in skill.action_registry.get_actions():
                usage = action.usage()
                actions.append(
                    f"- __{skill_name}.{usage.name}({', '.join([str(parameter) for parameter in usage.parameters])})__: _{usage.description}_"
                )
        if not actions:
            return "No actions available."

        action_string = "```markdown\n### Actions\n\n" + "\n".join(actions) + "\n```"
        # self.assistant._emit(InformationEvent(message=action_string))
        return action_string

    def run_action(self, designation: str, *args, **kwargs) -> Any:
        """
        Run an assistant action by designation (<skill_name>.<action_name>).
        """
        return self.assistant.run_action(designation, *args, **kwargs)

    def list_functions(self) -> list[Callable]:
        return [
            self.list_routines,
            self.run_routine,
            self.list_actions,
            self.run_action,
        ]
