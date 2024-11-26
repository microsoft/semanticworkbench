import logging
from typing import Any, Callable, Type

from events import BaseEvent, EventProtocol
from openai.types.chat.completion_create_params import ResponseFormat
from openai_client.chat_driver import ChatDriver, ChatDriverConfig
from openai_client.completion import TEXT_RESPONSE_FORMAT

from .actions import Action, Actions
from .routine import RoutineTypes

EmitterType = Callable[[EventProtocol], None]


def log_emitter(event: EventProtocol) -> None:
    logging.info(event)


class Skill:
    """
    Skills come with actions, routines, and, optionally, a conversational
    interface. Skills can be registered to assistants.
    """

    def __init__(
        self,
        name: str,
        description: str,
        actions: list[Callable] = [],  # Functions to be registered as skill actions.
        routines: list[RoutineTypes] = [],
        chat_driver_config: ChatDriverConfig | None = None,
    ) -> None:
        # A skill should have a short name so that user commands can be routed
        # to them efficiently.
        self.name = name
        self.description = description
        self.routines: dict[str, RoutineTypes] = {routine.name: routine for routine in routines}

        # The routines in this skill might use actions from other skills. The dependency on
        # other skills should be declared here. The skill registry will ensure that all
        # dependencies are registered before this skill.
        self.dependencies: list[Type[Skill]] = []

        # If a chat driver is provided, it will be used to respond to
        # conversational messages sent to the skill. Not all skills need to have
        # a chat driver. No functions will be automatically registered to the
        # chat driver. If you want to register a function with the chat driver,
        # do so when configuring the chat driver passed in (usually done in the
        # skill subclass).
        self.chat_driver = ChatDriver(chat_driver_config) if chat_driver_config else None

        # TODO: We maybe want to add actions to the skill's chat driver. If we
        # do, strip the RunContext param.

        # Register all provided actions with the action registry so they can be executed by name.
        self.action_registry = Actions()
        self.action_registry.add_functions(actions)

        # TODO: Is this helpful?
        # Also, register any commands provided by the chat driver. All
        # commands will be available to the skill.
        # if self.chat_driver:
        #     self.action_registry.add_functions(self.chat_driver.get_commands())

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
        return [function.fn for function in self.action_registry.get_actions()]

    def get_action(self, name: str) -> Action | None:
        return self.action_registry.get_action(name)

    def list_actions(self) -> list[str]:
        return [action.name for action in self.action_registry.get_actions()]

    def add_routine(self, routine: RoutineTypes) -> None:
        """
        Add a routine to the skill.
        """
        self.routines[routine.name] = routine

    def get_routine(self, name: str) -> RoutineTypes | None:
        """
        Get a routine by name.
        """
        return self.routines.get(name)

    def list_routines(self) -> list[str]:
        return [str(routine) for routine in self.routines.values()]

    def has_routine(self, name: str) -> bool:
        return name in self.routines

    def __str__(self) -> str:
        return f"{self.name} - {self.description}"

    def __repr__(self) -> str:
        return f"{self.name} - {self.description}"
