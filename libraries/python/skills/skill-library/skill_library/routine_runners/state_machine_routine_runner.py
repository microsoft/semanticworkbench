from typing import Any

from ..routine import StateMachineRoutine
from ..run_context import RunContext


class StateMachineRoutineRunner:
    def __init__(self) -> None:
        pass

    async def run(
        self, context: RunContext, routine: StateMachineRoutine, vars: dict[str, Any] | None = None
    ) -> tuple[bool, Any]:
        return await routine.init_function(context, vars)

    async def next(self, context: RunContext, routine: StateMachineRoutine, message: str) -> tuple[bool, Any]:
        """
        Run the next step in the current routine.
        """
        return await routine.step_function(context, message)
