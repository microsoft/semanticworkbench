from typing import Any

from ..routine import StateMachineRoutine
from ..run_context import RunContext


class StateMachineRoutineRunner:
    def __init__(self) -> None:
        pass

    async def run(self, context: RunContext, routine: StateMachineRoutine, vars: dict[str, Any] | None = None) -> Any:
        await routine.init_function(context, vars)

    async def next(self, context: RunContext, routine: StateMachineRoutine, message: str) -> Any:
        """
        Run the next step in the current routine.
        """
        await routine.step_function(context, message)
