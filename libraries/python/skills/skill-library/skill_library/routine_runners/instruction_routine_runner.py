from typing import Any

from events import BaseEvent, InformationEvent

from ..routine import InstructionRoutine
from ..run_context import RunContext


class InstructionRoutineRunner:
    def __init__(self) -> None:
        pass

    async def run(
        self, context: RunContext, routine: InstructionRoutine, vars: dict[str, Any] | None = None
    ) -> tuple[bool, Any]:
        """
        Run an Instruction routine. This just runs through the steps of a
        routine, sending each one to a skill's response endpoint. Note, this
        means this can only be used with skills that have been configured with a
        chat driver. This could be much more sophisticated, though. It might
        handle more configuration, manage results of steps, handle errors and
        retries, etc. Also, we might add meta-cognitive functions, tracking
        progress and changing steps as necessary.
        """
        # Replace mustache variables in the routine with the values from the vars dict.
        if vars:
            for key, value in vars.items():
                routine.routine = routine.routine.replace(f"{{{{ {key} }}}}", value)
                routine.routine = routine.routine.replace(f"{{{{{key}}}}}", value)

        # TODO: save a copy of this routine to run state.

        steps = routine.routine.split("\n")
        for step in steps:
            context.emit(InformationEvent(message=f"Running step: {step}"))
            response: BaseEvent = await routine.skill.respond(message=step)
            informationEvent = InformationEvent(**response.model_dump())
            context.emit(informationEvent)

        return True, None

    async def next(self, context: RunContext, routine: InstructionRoutine, message: str) -> tuple[bool, Any]:
        """
        Run the next step in the current routine.
        """
        return True, None
