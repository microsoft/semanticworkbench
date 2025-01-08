import re
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Optional, Tuple, Union

from skill_library.run_context import RunContext

if TYPE_CHECKING:
    pass


def find_template_vars(text: str) -> list[str]:
    """
    Find mustache template variables in a string. Variables will be
    de-duplicated and returned in order of first appearance.
    """
    matches = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")
    return list(set(matches.findall(text)))


class Routine:
    def __init__(
        self,
        name: str,
        skill_name: str,
        description: str,
    ) -> None:
        self.name = name
        self.skill_name = skill_name
        self.description = description

    def fullname(self) -> str:
        return f"{self.skill_name}.{self.name}"

    def __str__(self) -> str:
        return self.fullname()


class InstructionRoutine(Routine):
    def __init__(
        self,
        name: str,
        skill_name: str,
        description: str,
        routine: str,
    ) -> None:
        super().__init__(
            name=name,
            skill_name=skill_name,
            description=description,
        )
        self.routine = routine

    def template_vars(self) -> list[str]:
        return find_template_vars(self.routine)

    def __str__(self) -> str:
        template_vars = find_template_vars(self.routine)
        return f"{self.name}(vars: {template_vars}): {self.description}"


class ProgramRoutine(Routine):
    def __init__(
        self,
        name: str,
        skill_name: str,
        description: str,
        program: str,
    ) -> None:
        super().__init__(
            name=name,
            skill_name=skill_name,
            description=description,
        )
        self.program = program

    def __str__(self) -> str:
        template_vars = find_template_vars(self.program)
        return f"{self.name}(vars: {template_vars}): {self.description}"


class StateMachineRoutine(Routine):
    def __init__(
        self,
        name: str,
        skill_name: str,
        description: str,
        init_function: Callable[[RunContext, Any], Awaitable[Tuple[bool, Any]]],
        step_function: Callable[[RunContext, Optional[str]], Awaitable[Tuple[bool, Any]]],
    ) -> None:
        super().__init__(
            name=name,
            skill_name=skill_name,
            description=description,
        )
        self.init_function = init_function
        self.step_function = step_function

    def __str__(self) -> str:
        return f"{self.name}: {self.description}"


RoutineTypes = Union[InstructionRoutine, ProgramRoutine, StateMachineRoutine]
