from typing import TYPE_CHECKING, Any

from ..routine import ProgramRoutine
from ..skill import Skill

if TYPE_CHECKING:
    from ..assistant import Assistant


class ProgramRoutineRunner:
    def __init__(self, assistant: "Assistant") -> None:
        self.skill_registry = assistant.skill_registry
        self.context = assistant.context

    async def run(self, skill: Skill, routine: ProgramRoutine, vars: dict[str, Any] | None = None) -> Any:
        """
        This implementation is not yet working. It is a placeholder for the
        future implementation of running a program routine. A program routine
        is a routine written in Python that can be executed by the assistant.
        The routine will refer to any skill.action(args) that it needs.
        """
        # Replace mustache variables in the routine with the values from the vars dict.
        if vars:
            for key, value in vars.items():
                routine.program = routine.program.replace(f"{{{{ {key} }}}}", value)
                routine.program = routine.program.replace(f"{{{{{key}}}}}", value)

        # TODO: execute the program.

        return
