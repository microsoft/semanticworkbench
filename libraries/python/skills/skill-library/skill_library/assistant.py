import asyncio
from os import PathLike
from typing import Any, AsyncIterator
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

from .run_context import RunContext
from .skill import Skill
from .skill_registry import SkillRegistry


class Assistant:
    def __init__(
        self,
        name,
        assistant_id: str | None,
        chat_driver_config: ChatDriverConfig,
        drive_root: PathLike | None = None,
        metadrive_drive_root: PathLike | None = None,
        skills: list[Skill] = [],
    ) -> None:
        self.skill_registry: SkillRegistry = SkillRegistry()

        self.name = name

        if not assistant_id:
            assistant_id = str(uuid4())

        # Configure the assistant chat interface.
        if chat_driver_config.message_provider is None:
            chat_driver_config.message_provider = LocalMessageHistoryProvider(
                LocalMessageHistoryProviderConfig(session_id=assistant_id, formatter=format_with_liquid)
            )
        self.chat_driver = self._register_chat_driver(chat_driver_config)

        # Set up the assistant event queue.
        self._event_queue = asyncio.Queue()  # Async queue for events
        self._stopped = asyncio.Event()  # Event to signal when the assistant has stopped
        if skills:
            self.register_skills(skills)

        # The assistant drive can be used to read and write files to a
        # particular location. The assistant drive should be used for
        # assistant-specific data and not for general data storage.
        self.drive: Drive = Drive(
            DriveConfig(
                root=drive_root or f".data/{assistant_id}/assistant",
                default_if_exists_behavior=IfDriveFileExistsBehavior.OVERWRITE,
            )
        )

        # The assistant run context identifies the assistant session (session)
        # and provides necessary utilities to be used for this particular
        # assistant session. The run context is passed to the assistant's chat
        # driver commands and functions and all skill actions and routines that
        # are run by the assistant.
        self.run_context = RunContext(
            session_id=assistant_id or str(uuid4()),
            assistant_drive=self.drive,
            emit=self._emit,
            run_routine=self.skill_registry.run_routine_by_name,
            metadata_drive_root=metadrive_drive_root,
        )

    ######################################
    # Lifecycle and event handling
    ######################################

    async def wait(self) -> RunContext:
        """
        After initializing an assistant, call this method to wait for assistant
        events. While running, any events produced by the assistant can be
        accessed through the `events` property. When the assistant completes,
        this method returns the session_id of the assistant session.
        """

        await self._stopped.wait()
        return self.run_context

    def stop(self) -> None:
        self._stopped.set()  # Signal that we are stopping

    @property
    async def events(self) -> AsyncIterator[EventProtocol]:
        """
        This method is a generator that yields events produced by the assistant
        as they are emitted. The generator will continue to yield events until
        the assistant has completed AND all events have been emitted.
        """
        while not self._stopped.is_set() or not self._event_queue.empty():
            try:
                event = self._event_queue.get_nowait()
                yield event
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.005)

    def _emit(self, event: EventProtocol) -> None:
        event.session_id = self.run_context.session_id
        self._event_queue.put_nowait(event)

    async def put_message(self, message: str) -> None:
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
        if await self.run_context.routine_stack.peek():
            await self.step_active_routine(message)
        else:
            # Otherwise, send the message to the chat driver.
            response = await self.chat_driver.respond(message)
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
            "and a dictionary of vars to be replaced into the routines templates. "
            "These vars are like the routines' input.\n\n"
            "Available routines and their available vars: {routines}. "
        )

        chat_functions = ChatFunctions(self)
        functions = [chat_functions.list_routines, chat_functions.run_routine]
        config.commands = functions
        config.functions = functions
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

    def register_skills(self, skills: list[Skill]) -> None:
        """Register a skill with the assistant. You need to register all skills
        that an assistant uses at the same time so dependencies can be loaded in
        the correct order."""
        self.skill_registry.register_all_skills(skills)

    # def list_actions(self, context: Context) -> list[str]:
    #     """Lists all the actions the assistant is able to perform."""
    #     return self.skill_registry.list_actions()

    def list_routines(self) -> list[str]:
        """Lists all the routines the assistant is able to perform."""
        return self.skill_registry.list_routines()

    async def run_routine(self, name: str, vars: dict[str, Any] | None = None) -> Any:
        """
        Run an assistant routine by name (e.g. <skill_name>.<routine_name>).
        """
        await self.skill_registry.run_routine_by_name(self.run_context, name, vars)

    async def step_active_routine(self, message: str) -> None:
        """Run another step in the current routine."""
        await self.skill_registry.step_active_routine(self.run_context, message)


class ChatFunctions:
    """Chat driver functions need to be registered with a context as their first
    argument. The function name is used as their name and the function block
    comment is used as the function description.  This is a simple class to
    provide these things."""

    def __init__(self, assistant: Assistant) -> None:
        self.assistant = assistant

    def list_routines(self) -> list[str]:
        """Lists all the routines available in the assistant."""
        return self.assistant.list_routines()

    async def run_routine(self, name: str, vars: dict[str, Any] | None) -> Any:
        """
        Run an assistant routine.
        """
        await self.assistant.run_routine(name, vars)
