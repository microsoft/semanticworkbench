from typing import Any

from ..utilities import find_template_vars
from .routine import Routine


class ProgramRoutine(Routine):
    """
    A routine that is defined by a Python-like (a subset of Python) program. The
    program is a string that can be executed by the assistant. When run, the
    program routine will be interpreted and executed up until the first
    non-builtin function call. The program will the pause and the external
    function will be called using the run_action method. The result of the
    external function call will be passed back to the interpreter and the
    program will continue executing.

    Supported:
    - Variable assignments
    - If/elif/else statements
    - While loops
    - Break/continue
    - Return statements
    - Nested scopes
    - Early returns from nested scopes
    - many built-in functions (str, int, float, bool, list, dict, len, range,
      zip, enumerate, sum, min, max, all, any, json.dumps, etc.)
    - some custom functions:
        - ask_user
        - print
        - last_message

    Not supported:
    - function definitions
    - functions returning functions
    - recursive functions
    - exception handling
    """

    def __init__(
        self,
        name: str,
        skill_name: str,
        description: str,
        program: str,
    ) -> None:
        super().__init__(
            name=name,
            skill_name=skill_name,
            description=description,
        )
        self.program = program

    def validate(self, arg_set: dict[str, Any]) -> None:
        """
        Validate the routine with the given arguments.
        """
        # All of the routines template variables should be defined in the arg set.
        template_vars = find_template_vars(self.program)
        missing_vars = [var for var in template_vars if var not in arg_set]
        if missing_vars:
            raise ValueError(f"Missing variables in arg set: {missing_vars}")

    def __str__(self) -> str:
        template_vars = find_template_vars(self.program)
        return f"{self.name}(vars: {template_vars}): {self.description}"
