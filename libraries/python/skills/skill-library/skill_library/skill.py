import logging
from typing import Any, Callable, Type

from attr import dataclass
from events import BaseEvent, EventProtocol
from openai.types.chat.completion_create_params import ResponseFormat
from openai_client.chat_driver import ChatDriver, ChatDriverConfig
from openai_client.completion import TEXT_RESPONSE_FORMAT

from .actions import Action, Actions
from .routine import RoutineTypes
from .run_context import RunContextProvider

EmitterType = Callable[[EventProtocol], None]


def log_emitter(event: EventProtocol) -> None:
    logging.info(event)


@dataclass
class SkillDefinition:
    name: str
    skill_class: Type["Skill"]
    description: str
    chat_driver_config: ChatDriverConfig | None


class Skill:
    """
    Skills come with actions, routines, and, optionally, a conversational
    interface. Skills can be registered to assistants.
    """

    def __init__(
        self,
        skill_definition: SkillDefinition,
        run_context_provider: RunContextProvider,
        actions: list[Callable] = [],  # Functions to be registered as skill actions.
        routines: list[RoutineTypes] = [],
    ) -> None:
        # A skill should have a short name so that user commands can be routed
        # to them efficiently.
        self.name = skill_definition.name
        self.description = skill_definition.description
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
        self.chat_driver = (
            ChatDriver(skill_definition.chat_driver_config) if skill_definition.chat_driver_config else None
        )

        # Register all provided actions with the action registry so they can be executed by name.
        self.action_registry = Actions(run_context_provider)
        self.action_registry.add_functions(actions)

        # Make actions available to be called as attributes from the skill
        # directly.
        self.actions = self.action_registry.functions

        # Actions and routines can get a RunContext whenever they want.
        self.run_context_provider = run_context_provider

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

    def get_routines(self) -> list[RoutineTypes]:
        """
        Return a list of routines.
        """
        return [routine for routine in self.routines.values()]

    def list_routines(self) -> list[str]:
        """Return a list of routine names."""
        return [str(routine) for routine in self.routines.values()]

    def has_routine(self, name: str) -> bool:
        return name in self.routines

    def __str__(self) -> str:
        return f"{self.name} - {self.description}"

    def __repr__(self) -> str:
        return f"{self.name} - {self.description}"
