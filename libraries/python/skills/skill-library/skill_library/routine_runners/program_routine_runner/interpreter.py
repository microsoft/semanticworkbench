import ast
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

    def get_state(self) -> str:
        """Get serializable state of the interpreter."""
        if self.transformed_code is None:
            raise RuntimeError("No code has been transformed yet")

        state = InterpreterState(cache_data=self.function_cache.serialize(), transformed_code=self.transformed_code)
        return state.serialize()

    @classmethod
    def from_state(
        cls,
        state_data: str,
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
        """Handles function calls amd caches results."""
        try:
            return self.function_cache.get(func_name, args, kwargs)
        except KeyError:
            # If this is a known function (passed in via globals), call it.
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

    def load_code(self, code: str) -> "Interpreter":
        """Load and parse source code."""
        tree: ast.Module = ast.parse(code)
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

        # Add the handle_function_call function to the globals. The compiler
        # will replace non-builtin function calls with a call to this function.
        # This is how we pause execution so we can handle external functions.
        exec_globals = {
            **self.globals,
            "handle_function_call": self.handle_function_call,
        }

        # Compile and execute the transformed code. This results in giving us a
        # new main function that will call handle_function_call when it
        # encounters an external function.
        exec(compile(compile_me, filename="<ast>", mode="exec"), exec_globals)
        if "main" not in exec_globals or not isinstance(exec_globals["main"], types.FunctionType):
            raise RuntimeError("Error: A `main` function is required.")

        # Here's the function to call to kick things off!
        self.main_func = exec_globals["main"]

        # Now enter the execution loop
        while True:
            result = None
            try:
                # Call the routine. If it hits an external function, it will
                # call `handle_function_call`` which will raise
                # `PausedExecution` and get us back here.
                #
                # handle_function_call takes care of caching results from
                # external function calls. We use the function name and it's
                # args as a cache key so only functions with the exact same name
                # and args will be cached. Once they are run, they won't be
                # paused again, their value is just used.
                #
                # We run the entire function over and over until it
                # passes without pausing (that's why we're in a while loop).
                result = self.main_func()
            except PausedExecution as pause_info:
                # Yield pause info back to the caller
                # ('program_routine_runner'). We'll wait for a response from
                # them. Note that this is running in memory. If the service
                # restarts, we'll never resume here. Also, this limits us to
                # running on a single process... which is probably not what we
                # want for a production system.
                yield pause_info
                continue

            # If we get here, main_func completed without pausing. We can yield a ReturnValue if we got one, or just None.
            if isinstance(result, ReturnValue):
                yield result

            break
