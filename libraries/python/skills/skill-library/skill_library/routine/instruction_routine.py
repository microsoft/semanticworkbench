from ..utilities import find_template_vars
from .routine import Routine


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
        return f"{self.fullname}(vars: {template_vars}): {self.description}"
