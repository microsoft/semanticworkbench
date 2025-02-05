from typing import Any, Callable, Dict, Union

from skill_library.routine_runners.program.function_cache import FunctionCache

ProgramLoggerType = Callable[[str], None]


class ReturnValue:
    """Wrapper class for return values from executed functions."""

    def __init__(self, value: Any):
        self.value = value


class PausedExecution(Exception):
    """Exception to indicate execution pause for unknown functions."""

    def __init__(self, func_name: str, args: tuple, kwargs: Dict[str, Any]) -> None:
        self.func_name = func_name
        self.args = args
        self.kwargs = kwargs
        self.cache_key = FunctionCache.get_cache_key(args, kwargs)


ReturnResult = Union[ReturnValue, PausedExecution]
