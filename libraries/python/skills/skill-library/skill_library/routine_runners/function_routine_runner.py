from typing import Any

from ..routine import FunctionRoutine
from ..run_context import RunContext


class FunctionRoutineRunner:
    def __init__(self) -> None:
        pass

    async def run(
        self, context: RunContext, routine: FunctionRoutine, vars: dict[str, Any] | None = None
    ) -> Any:
        routine.init_function(context, vars)

    async def next(self, context: RunContext, routine: FunctionRoutine, message: str) -> Any:
        """
        Run the next step in the current routine.
        """
        routine.step_function(context, message)
