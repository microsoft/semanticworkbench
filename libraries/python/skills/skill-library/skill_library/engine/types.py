from typing import Any, Awaitable, Callable

from .run_context import RunContext

AskUserFn = Callable[[str], Awaitable[str]]
PrintFn = Callable[[str], Awaitable[None]]
ActionFn = Callable[[RunContext], Awaitable[Any]]
RoutineFn = Callable[[RunContext, AskUserFn, PrintFn], Awaitable[Any]]
