from typing import Any, Callable

import pytest
from context.context import Context
from function_registry.function_registry import FunctionRegistry


def no_op(context: Context) -> None:
    pass


def echo(context: Context, value: Any) -> str:
    match value:
        case str():
            return value
        case list():
            return ", ".join(map(str, value))
        case dict():
            return ", ".join(f"{k}: {v}" for k, v in value.items())
        case int() | bool() | float():
            return str(value)
        case _:
            return str(value)


context = Context()
functions = [echo, no_op]
register = FunctionRegistry(functions)


@pytest.mark.parametrize(
    "command_string, expected_command, expected_args, expected_kwargs, expected_error",
    [
        # Simplest case.
        ("no_op()", "no_op", [], {}, None),
        # Args.
        ('/echo("Hello!")', "echo", ["Hello!"], {}, None),
        ("/echo(42)", "echo", [42], {}, None),
        ("/echo(42.0)", "echo", [42.0], {}, None),
        ("/echo(True)", "echo", [True], {}, None),
        ("/echo([1, 2, 3])", "echo", [[1, 2, 3]], {}, None),
        ('/echo({"a": 1, "b": 2})', "echo", [{"a": 1, "b": 2}], {}, None),
        # Keyword args.
        ('/echo(value="Hello!")', "echo", [], {"value": "Hello!"}, None),
        ("/echo(value=42)", "echo", [], {"value": 42}, None),
        ("/echo(value=42.0)", "echo", [], {"value": 42.0}, None),
        ("/echo(value=True)", "echo", [], {"value": True}, None),
        ("/echo(value=[1, 2, 3])", "echo", [], {"value": [1, 2, 3]}, None),
        ('/echo(value={"a": 1, "b": 2})', "echo", [], {"value": {"a": 1, "b": 2}}, None),
        # No cmd prefix.
        ('echo("Hello!")', "echo", ["Hello!"], {}, None),
        # Unregistered command.
        ('unregistered("Hello!")', None, [], {}, None),
        # Invalid args.
        ("/echo(Hello!)", None, [], {}, ValueError),
    ],
)
def test_command_parsing_pythonic(
    command_string: str,
    expected_command: Callable,
    expected_args: list[Any],
    expected_kwargs: dict[str, Any],
    expected_error: Any,
):
    try:
        command, args, kwargs = register.parse_function_string(command_string)
    except Exception as e:
        assert expected_error is not None
        assert isinstance(e, expected_error)
        return

    if command is None:
        assert expected_command is None
    else:
        assert command.name == expected_command

    assert args == expected_args
    assert kwargs == expected_kwargs
