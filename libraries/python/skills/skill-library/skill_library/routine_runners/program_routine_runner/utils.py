import inspect
from textwrap import dedent
from typing import Callable


def get_function_source(func: Callable) -> str:
    """Get the source code of a function."""
    return dedent(inspect.getsource(func))
