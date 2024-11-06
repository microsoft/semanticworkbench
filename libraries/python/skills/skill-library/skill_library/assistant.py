import asyncio
from typing import Any, AsyncIterator

from chat_driver import TEXT_RESPONSE_FORMAT, ChatDriver, ChatDriverConfig, ResponseFormat
from context import Context
from events import BaseEvent, EventProtocol

from .routine import InstructionRoutine, ProgramRoutine
from .routine_runners import InstructionRoutineRunner, ProgramRoutineRunner
from .skill import Skill
from .skill_registry import SkillRegistry


class Assistant:
    def __init__(
        self,
        name,
        chat_driver_config: ChatDriverConfig,
        session_id: str | None = None,
    ) -> None:
        self.name = name
        self.skill_registry = SkillRegistry()
        self.chat_driver = self._register_chat_driver(chat_driver_config)
        self._event_queue = asyncio.Queue()  # Async queue for events
        self._stopped = asyncio.Event()  # Event to signal when the assistant has stopped
        self._running_routines = {}
        self.context = Context(session_id=session_id, emit=self._emit)

    ######################################
    # Lifecycle and event handling
    ######################################

    async def wait(self) -> Context:
        """
        After initializing an assistant, call this method to wait for assistant
        events. While running, any events produced by the assistant can be
        accessed through the `events` property. When the assistant completes,
        this method returns the session_id of the assistant session.
        """

        await self._stopped.wait()
        return self.context

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
        event.session_id = self.context.session_id
        self._event_queue.put_nowait(event)

    async def put_message(self, message: str) -> None:
        """Exposed externally for sending messages to the assistant."""
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
        if self.chat_driver:
            for skill in skills:
                self.chat_driver.register_functions(skill.get_chat_functions())
                self.chat_driver.register_commands(skill.get_chat_commands())

    # def list_actions(self, context: Context) -> list[str]:
    #     """Lists all the actions the assistant is able to perform."""
    #     return self.skill_registry.list_actions()

    def list_routines(self) -> list[str]:
        """Lists all the routines the assistant is able to perform."""
        return self.skill_registry.list_routines()

    async def run_routine(self, name: str, vars: dict[str, Any] | None = None) -> Any:
        """
        Run an assistant routine. This is going to be much of the
        magic of the assistant. Currently, is just runs through the
        steps of a routine, but this will get much more sophisticated.
        It will need to handle configuration, managing results of steps,
        handling errors and retries, etc. ALso, this is where we will put
        meta-cognitive functions such as having the assistant create a plan
        from the routine and executing it dynamically while monitoring progress.
        """
        skill, routine = self.skill_registry.get_routine(name)
        if not skill:
            raise ValueError(f"Skill {name} not found.")
        if not routine:
            raise ValueError(f"Routine {name} not found.")

        match routine:
            case InstructionRoutine():
                runner = InstructionRoutineRunner(self)
                return await runner.run(skill, routine, vars)
            case ProgramRoutine():
                runner = ProgramRoutineRunner(self)
                return await runner.run(skill, routine, vars)


class ChatFunctions:
    """Chat driver functions need to be registered with a context as their first
    argument. The function name is used as their name and the function block
    comment is used as the function description.  This is a simple class to
    provide these things."""

    def __init__(self, assistant: Assistant) -> None:
        self.assistant = assistant

    def list_routines(self, context: Context) -> list[str]:
        """Lists all the routines available in the assistant."""
        return self.assistant.list_routines()

    async def run_routine(self, context: Context, name: str, vars: dict[str, Any] | None = None) -> Any:
        """
        Run an assistant routine.
        """
        await self.assistant.run_routine(name, vars)
