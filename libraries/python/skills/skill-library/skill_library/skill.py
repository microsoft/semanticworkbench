from typing import Any, Callable

from chat_driver import TEXT_RESPONSE_FORMAT, ChatDriver, ChatDriverConfig, ContextProtocol
from events import BaseEvent
from function_registry import FunctionRegistry
from openai.types.chat.completion_create_params import ResponseFormat

from .routine import RoutineTypes


class Skill:
    """
    Skills come with actions, routines, and, optionally, a conversational
    interface. Skills can be registered to assistants.
    """

    def __init__(
        self,
        name: str,
        description: str,
        context: ContextProtocol,
        chat_driver_config: ChatDriverConfig | None = None,
        skill_actions: list[Callable] = [],  # Functions to be registered as skill actions.
        routines: list[RoutineTypes] = [],
    ) -> None:
        # A skill should have a short name so that user commands can be routed
        # to them efficiently.
        self.name = name
        self.description = description
        self.routines: dict[str, RoutineTypes] = {routine.name: routine for routine in routines}

        # The routines in this skill might use actions from other skills. The dependency on
        # other skills should be declared here. The skill registry will ensure that all
        # dependencies are registered before this skill.
        self.dependencies: list[str] = []

        # If a chat driver is provided, it will be used to respond to
        # conversational messages sent to the skill. Not all skills need to have
        # a chat driver. No functions will be automatically registered to the
        # chat driver. If you want to register a function with the chat driver,
        # do so when configuring the chat driver passed in (usually done in the
        # skill subclass).
        self.chat_driver = ChatDriver(chat_driver_config) if chat_driver_config else None

        # TODO: Configure up one of these separate from the chat driver.
        self.openai_client = chat_driver_config.openai_client if chat_driver_config else None

        # Register all provided actions with the action registry.
        self.action_registry = FunctionRegistry(context, skill_actions)

        # Also, register any commands provided by the chat driver. All
        # commands will be available to the skill.
        if self.chat_driver:
            self.action_registry.register_functions(self.chat_driver.get_commands())

        # Make actions available to be called as attributes from the skill
        # directly.
        self.actions = self.action_registry.functions

    async def respond(
        self,
        message: str,
        response_format: ResponseFormat = TEXT_RESPONSE_FORMAT,
        instruction_parameters: dict[str, Any] | None = None,
    ) -> BaseEvent:
        """
        Respond to a user message if the skill has a chat driver.
        """
        if not self.chat_driver:
            raise ValueError("No assistant found for this skill to use for responding.")
        return await self.chat_driver.respond(
            message,
            response_format=response_format,
            instruction_parameters=instruction_parameters,
        )

    def get_actions(self) -> list[Callable]:
        return [function.fn for function in self.action_registry.get_functions()]

    def list_actions(self) -> list[str]:
        return self.action_registry.list_functions()

    def add_routine(self, routine: RoutineTypes) -> None:
        """
        Add a routine to the skill.
        """
        self.routines[routine.name] = routine

    def get_routine(self, name: str) -> RoutineTypes | None:
        """
        Get a routine by name.
        """
        return self.routines[name]

    def list_routines(self) -> list[str]:
        return [str(routine) for routine in self.routines.values()]

    def has_routine(self, name: str) -> bool:
        return name in self.routines

    # Convenience methods for getting the chat driver's functions and commands.

    def get_chat_functions(self) -> list[Callable]:
        if not self.chat_driver:
            return []
        return self.chat_driver.get_functions()

    def get_chat_commands(self) -> list[Callable]:
        if not self.chat_driver:
            return []
        return self.chat_driver.get_commands()

    def __str__(self) -> str:
        return f"{self.name} - {self.description}"

    def __repr__(self) -> str:
        return f"{self.name} - {self.description}"
