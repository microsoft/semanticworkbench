from typing import Any, Awaitable, Callable, Concatenate, ParamSpec

P = ParamSpec("P")
RunActionType = Callable[Concatenate[str, P], Awaitable[Any]]


# Implementation.
async def run_action(designation: str, *args: Any, **kwargs: Any) -> Any:
    return designation, args, kwargs


# Assignment.
run_action_var: RunActionType = run_action


async def test_paramspec():
    result = await run_action_var(
        "test_designation",
        1,
        2,
        3,
        key1="value1",
        key2=42,
    )
    assert result == ("test_designation", (1, 2, 3), {"key1": "value1", "key2": 42})


async def test_paramspec_with_dictionary():
    result = await run_action_var(
        "test_designation",
        1,
        2,
        3,
        **{"key1": "value1", "key2": 42},
    )
    assert result == ("test_designation", (1, 2, 3), {"key1": "value1", "key2": 42})


async def test_paramspec_with_no_args():
    d: dict[str, Any] = {"key1": "value1", "key2": 42}
    result = await run_action_var(
        "test_designation",
        **d,
    )
    assert result == ("test_designation", (), {"key1": "value1", "key2": 42})
