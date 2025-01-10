from ..utilities import find_template_vars
from .routine import Routine


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
