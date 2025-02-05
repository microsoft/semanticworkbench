import ast
import builtins
import logging
import types
from typing import Any, Callable, Generator, Union

from .function_cache import FunctionCache
from .function_interceptor import FunctionInterceptor
from .interpreter_state import InterpreterState
from .types import PausedExecution, ProgramLoggerType, ReturnValue
from .utils import get_function_source


class Interpreter:
    def __init__(self, program_logger: ProgramLoggerType | None = None) -> None:
        # Set up logging.
        if program_logger is None:
            logger = logging.getLogger(__name__)

            def default_logger(msg: str):
                logger.debug(msg)

            self.program_logger = default_logger
        else:
            self.program_logger = program_logger

        self.globals = {}
        self.main_func = None
        self.function_cache = FunctionCache()
        self.transformed_code: str | None = None

    # Persistence methods

    def get_state(self) -> bytes:
        """Get serializable state of the interpreter."""
        if self.transformed_code is None:
            raise RuntimeError("No code has been transformed yet")

        state = InterpreterState(cache_data=self.function_cache.serialize(), transformed_code=self.transformed_code)
        return state.serialize()

    @classmethod
    def from_state(
        cls,
        state_data: bytes,
        program_logger: ProgramLoggerType | None = None,
    ) -> "Interpreter":
        """Create a new Interpreter instance from serialized state."""
        state = InterpreterState.deserialize(state_data)
        interpreter = cls(program_logger)
        interpreter.function_cache = FunctionCache.deserialize(state.cache_data)
        interpreter.transformed_code = state.transformed_code
        return interpreter

    ## External function (actions) handling.

    def handle_function_call(self, func_name: str, *args: Any, **kwargs: Any) -> Any:
        """Handles function calls, supporting built-ins and caching results."""
        if func_name in builtins.__dict__:
            return builtins.__dict__[func_name](*args, **kwargs)

        try:
            return self.function_cache.get(func_name, args, kwargs)
        except KeyError:
            if func_name in self.globals:
                return self.globals[func_name](*args, **kwargs)
            raise PausedExecution(func_name, args, kwargs)

    def add_function_result(self, func_name: str, cache_key: tuple, result: Any) -> None:
        """Add a function result to the cache."""
        self.function_cache.set_with_cache_key(func_name, cache_key, result)

    def load_function(self, func: Callable) -> "Interpreter":
        """Load a function into the interpreter."""
        self.globals[func.__name__] = func
        source = get_function_source(func)
        self.load_code(source)
        return self

    def load_code(self, source_code: str) -> "Interpreter":
        """Load and parse source code."""
        tree: ast.Module = ast.parse(source_code)
        transformer: FunctionInterceptor = FunctionInterceptor()
        new_tree: ast.Module = transformer.visit(tree)
        ast.fix_missing_locations(new_tree)
        self.transformed_code = ast.unparse(new_tree)
        return self

    def execute_with_pausing(self) -> Generator[Union[PausedExecution, Any], None, None]:
        """
        Executes Python code as a generator, pausing on unknown function calls.
        Yields either PausedExecution instances or the final return value.

        Args:
            code: The source code to execute
            transform: Whether to transform the code (False if code is already transformed)
        """

        if self.transformed_code is None:
            raise RuntimeError("No transformed code available")
        compile_me = ast.parse(self.transformed_code)

        exec_globals = {
            **self.globals,
            "handle_function_call": self.handle_function_call,
            "ReturnValue": ReturnValue,
        }

        # Compile and execute the transformed code
        exec(compile(compile_me, filename="<ast>", mode="exec"), exec_globals)

        # Store the main function
        if "main" not in exec_globals or not isinstance(exec_globals["main"], types.FunctionType):
            raise RuntimeError("Error: A `main` function is required.")

        self.main_func = exec_globals["main"]

        # Now enter the execution loop
        while True:
            try:
                result = self.main_func()
                if isinstance(result, ReturnValue):
                    yield result
                else:
                    yield None
                break  # Exit after successful completion
            except PausedExecution as e:
                yield e  # Yield pause and continue with updated function cache
