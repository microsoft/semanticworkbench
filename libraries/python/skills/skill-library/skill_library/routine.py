import re
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict, Optional, Union

from skill_library.run_context import RunContext

if TYPE_CHECKING:
    from skill_library.skill import Skill


def find_template_vars(text: str) -> list[str]:
    """
    Find mustache template variables in a string.
    """
    matches = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")
    return sorted(list(set(matches.findall(text))))


class Routine:
    def __init__(
        self,
        name: str,
        description: str,
        skill: "Skill",
    ) -> None:
        self.name = name
        self.description = description
        self.skill = skill

    def fullname(self) -> str:
        return f"{self.skill.name}.{self.name}"

    def __str__(self) -> str:
        return self.fullname()


class InstructionRoutine(Routine):
    def __init__(
        self,
        name: str,
        description: str,
        routine: str,
        skill: "Skill",
    ) -> None:
        super().__init__(
            name=name,
            description=description,
            skill=skill,
        )
        self.routine = routine

    def __str__(self) -> str:
        template_vars = find_template_vars(self.routine)
        return f"{self.name}(vars: {template_vars}): {self.description}"


class ProgramRoutine(Routine):
    def __init__(
        self,
        name: str,
        description: str,
        program: str,
        skill: "Skill",
    ) -> None:
        super().__init__(
            name=name,
            description=description,
            skill=skill,
        )
        self.program = program

    def __str__(self) -> str:
        template_vars = find_template_vars(self.program)
        return f"{self.name}(vars: {template_vars}): {self.description}"


class StateMachineRoutine(Routine):
    def __init__(
        self,
        name: str,
        description: str,
        init_function: Callable[[RunContext, Optional[Dict[str, Any]]], Awaitable[None]],
        step_function: Callable[[RunContext, Optional[str]], Awaitable[Optional[Any]]],
        skill: "Skill",
    ) -> None:
        super().__init__(
            name=name,
            description=description,
            skill=skill,
        )
        self.init_function = init_function
        self.step_function = step_function

    def __str__(self) -> str:
        return f"{self.name}: {self.description}"


RoutineTypes = Union[InstructionRoutine, ProgramRoutine, StateMachineRoutine]
