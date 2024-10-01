from typing import Union
import re


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
    ) -> None:
        self.name = name
        self.description = description


class InstructionRoutine(Routine):
    def __init__(
        self,
        name: str,
        description: str,
        routine: str,
    ) -> None:
        super().__init__(
            name=name,
            description=description,
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
    ) -> None:
        super().__init__(
            name=name,
            description=description,
        )
        self.program = program

    def __str__(self) -> str:
        template_vars = find_template_vars(self.program)
        return f"{self.name}(vars: {template_vars}): {self.description}"


RoutineTypes = Union[InstructionRoutine, ProgramRoutine]
