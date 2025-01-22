from typing import Any, Awaitable, Callable, Optional, Tuple

from skill_library.run_context import RunContext

from .routine import Routine


class StateMachineRoutine(Routine):
    def __init__(
        self,
        name: str,
        skill_name: str,
        description: str,
        init_function: Callable[[RunContext, Any], Awaitable[Tuple[bool, Any]]],
        step_function: Callable[[RunContext, Optional[str]], Awaitable[Tuple[bool, Any]]],
    ) -> None:
        super().__init__(
            name=name,
            skill_name=skill_name,
            description=description,
        )
        self.init_function = init_function
        self.step_function = step_function

    def __str__(self) -> str:
        return f"{self.name}: {self.description}"
