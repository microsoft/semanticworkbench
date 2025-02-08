import inspect
from textwrap import dedent
from typing import Any, Callable

from ..utilities import find_template_vars
from .routine import Routine


class ProgramRoutine(Routine):
    """
    A routine that is defined by a Python program. The program will be executed
    by the assistant. When run, the program routine will be interpreted and
    executed up until the first non-builtin function call. The program will the
    pause and the external function will be called using the run_action method.
    The result of the external function call will be passed back to the
    interpreter and the program will resume execution.

    ## Writing a Program Routine

    The program must have a `main` function that will be called to start the
    program.

    You can define the program with a string, or use the `get_function_source`
    function below to convert a function (the `main` function) into a string.

    You will have to mock any external functions that are called in the program
    so that the program can be linted. To make this simple, you can use the
    `ExternalFunctionMock` class below to mock the functions. The program will
    call the real functions when it is executed.

    See the [Program Routine
    Runner](../routine_runners/program_routine_runner/program_routine_runner.py)
    to see how the program is executed.

    ## Loop Variables

    Each time the program is run, it is executed from the beginning. This makes
    the interpreter simpler since we don't have to track our position in the
    program and all variables scopes to that position to resume. To make this
    work, the interpreter keeps a cache of previously run function calls and
    will use the cached result if the function is called with the same arguments
    again.

    This means one important way these programs differ from normal Python
    programs is that they any external function calls inside loops need to
    include the loop variable in the arguments to the function. Otherwise, the
    function will be called once and the result will be cached and used for all
    iterations of the loop, which is probably not what you want.

    ## Program source variables

    The programs can also use mustache variables replacement to insert values
    into the program before it is executed. The mustache variables should be
    defined in the arg set that is passed to the program runner. The end result
    is that any arguments you pass into the `run_action` method will be
    available in the program as mustache variables. This allows you to run the
    same program routine with different arguments. For example, the when working
    with an assistant, if you use the command
    `/run_routine("my_program_routine", {"name": "John"})`, the program will
    have access to the variable `name` with the value `"John"` and will replace
    `{{name}}` with `"John"` in the program source code before executing it.
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


def get_function_source(func: Callable) -> str:
    """Get the source code of a function."""
    return dedent(inspect.getsource(func))


class ExternalFunctionMock:
    """
    Program Routines store the source code for a routine that you would like
    executed. One way to provide that source code is to write a `main` function
    and then use `get_function_source` to get the source code of that function.
    This class is used to mock the functions that are called in the `main`
    function so it passes linting. Simply define any function that doesn't lint
    (which will be executed for real by the program_runner) and assign it a
    mock. This is good enough for being able to generate the source code for the
    routine.
    """

    def __getattr__(self, _: str) -> Any:
        return lambda *args, **kwargs: None
