"""Program runner interface.

This module provides a simplified interface for executing routines with user interaction
capabilities. It allows routines to be async functions that can pause execution to await
user input.
"""

from asyncio import Future
from dataclasses import dataclass
from typing import Any

from events import InformationEvent, MessageEvent

from .routine_stack import RoutineStack
from .run_context import RunContext
from .types import RoutineFn


@dataclass
class RoutineRunner:
    """Executes routines with support for user interaction.

    This runner executes a given async function (routine) while providing it access
    to run_context and an ask_user function. The routine can await ask_user to pause
    execution and wait for user input.

    Example routine:
        async def my_routine(run_context: RunContext, ask_user: AskUserFn) -> str:
            name = await ask_user("What's your name?")
            return f"Hello {name}!"
    """

    def __init__(self, routine_stack: RoutineStack) -> None:
        self._current_future: Future | None = None
        self.routine_stack = routine_stack

    async def start(self, run_context: RunContext, routine: RoutineFn, *args: Any, **kwargs: Any) -> Any:
        """Start execution of a routine.
        Args:
            run_context: The execution context
            routine: Async function to execute
            *args: Positional arguments to pass to routine
            **kwargs: Keyword arguments to pass to routine
        """
        try:
            # Create ask_user function with access to runner state
            async def ask_user(prompt: str) -> str:
                self._current_future = Future()
                run_context.emit(MessageEvent(message=prompt))
                return await self._current_future

            async def print(message: str) -> None:
                self._current_future = Future()
                run_context.emit(InformationEvent(message=message))

            # Add run_context and ask_user to routine kwargs
            routine_kwargs = {
                "run_context": run_context,
                "ask_user": ask_user,
                "print": print,
                **kwargs,
            }

            # Execute routine
            await self.routine_stack.push(routine.__name__)
            result = await routine(*args, **routine_kwargs)
            await self.routine_stack.pop()
            return result

        except Exception as e:
            run_context.emit(InformationEvent(message=f"Error executing routine: {str(e)}"))
            return True

    def resume(self, message: str) -> None:
        """Resume execution with user input."""
        if self._current_future and not self._current_future.done():
            self._current_future.set_result(message)
