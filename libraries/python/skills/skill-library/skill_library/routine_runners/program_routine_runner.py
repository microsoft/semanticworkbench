from typing import Any

from ..routine import ProgramRoutine
from ..run_context import RunContext


class ProgramRoutineRunner:
    def __init__(self) -> None:
        pass

    async def run(self, context: RunContext, routine: ProgramRoutine, *args: Any, **kwargs: Any) -> tuple[bool, Any]:
        """
        This implementation is not yet working. It is a placeholder for the
        future implementation of running a program routine. A program routine
        is a routine written in Python that can be executed by the assistant.
        The routine will refer to any skill.action(args) that it needs.
        """

        # TODO: Unimplemented routine.

        return True, None

    async def next(self, context: RunContext, routine: ProgramRoutine, message: str) -> tuple[bool, Any]:
        """
        Run the next step in the current routine.
        """
        return True, None
