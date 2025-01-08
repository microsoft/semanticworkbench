from typing import Any


def make_arg_set(expected_variables: list[str], args: tuple, kwargs: dict[str, Any]) -> dict[str, Any]:
    """
    Make a dictionary out of args and kwargs that aligns with expected
    variables. The result will be a dictionary containing the expected variables
    as keys and the args and kwargs as values. kwargs take precedence over args
    (they will overwrite).
    """
    arg_set = {}

    # Align any args with the expected variables.
    if args:
        for index, value in enumerate(args):
            if index < len(expected_variables):
                arg_set[expected_variables[index]] = value

    # Overwrite any args that were already set (kwargs take precedence). Only
    # include kwargs that are in the expected variables.
    kwargs_set = {key: value for key, value in kwargs.items() if key in expected_variables}
    arg_set.update(kwargs_set)
    return arg_set
