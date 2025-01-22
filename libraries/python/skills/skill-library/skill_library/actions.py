import inspect
from dataclasses import dataclass
from typing import Any, Protocol

from .run_context import RunContext, RunContextProvider
from .utilities import parse_command_string


class ActionCallable(Protocol):
    def __call__(self, run_context: RunContext, *args: Any, **kwargs: Any) -> Any: ...

    __name__: str


@dataclass
class Parameter:
    """
    Tool functions are described by their parameters. This dataclass
    describes a single parameter of a tool function.
    """

    name: str
    type: Any
    description: str | None
    default_value: Any | None = None

    def __str__(self) -> str:
        param_type = self.type
        try:
            param_type = self.type.__name__
        except AttributeError:
            param_type = self.type
        usage = f"{self.name}: {param_type}"
        if self.default_value is not inspect.Parameter.empty:
            if isinstance(self.default_value, str):
                usage += f' = "{self.default_value}"'
            else:
                usage += f" = {self.default_value}"
        return usage


@dataclass
class Usage:
    """
    A usage string for this function. This can be used in help messages.
    """

    name: str
    parameters: list[Parameter]
    description: str

    def __str__(self) -> str:
        param_usage = ", ".join(str(param) for param in self.parameters)
        return f"{self.name}({param_usage}): {self.description}"


class Action:
    """
    An action is a Python function that can be called as part of a skill. This
    class wraps a function and provides metadata about it. It also provides a
    way to execute the action with a RunContext.
    """

    def __init__(self, fn: ActionCallable, name: str | None = None, description: str | None = None) -> None:
        self.fn = fn
        self.name = name or fn.__name__
        self.description = description or inspect.getdoc(fn) or self.name.replace("_", " ").title()

    def parameters(self, exclude: list[str] = []) -> list[Parameter]:
        """
        This function's parameters and their default values.
        """
        parameters = dict(inspect.signature(self.fn).parameters)
        for param_name in exclude:
            if param_name in parameters:
                del parameters[param_name]
        return [
            Parameter(
                name=param_name,
                type=param.annotation,
                description=None,  # param.annotation.description,
                default_value=param.default,
            )
            for param_name, param in parameters.items()
        ]

    def usage(self) -> Usage:
        """
        A usage string for this function. This can be used in help messages.
        """
        return Usage(name=self.name, parameters=self.parameters(exclude=["run_context"]), description=self.description)

    async def execute(self, run_context: RunContext, *args: Any, **kwargs: Any) -> Any:
        """
        Run this action, and return its value. If the function is a coroutine,
        it will be awaited.
        """
        result = self.fn(run_context, *args, **kwargs)
        if inspect.iscoroutine(result):
            result = await result
        return result


class ActionHandler:
    def __init__(self, actions: "Actions") -> None:
        self.actions = actions

    def __getattr__(self, name: str) -> ActionCallable:
        """Makes registered functions accessible as attributes of the Actions object."""
        if name not in self.actions.action_map:
            raise AttributeError(f"No action named '{name}'")

        async def wrapper(*args, **kwargs) -> Any:
            return await self.actions.run_action_by_name(name, args, kwargs)

        return wrapper


class Actions:
    """
    A set of a skill's actions.
    """

    def __init__(
        self, run_context_provider: RunContextProvider, actions: list[Action] | None = None, with_help: bool = False
    ) -> None:
        # Set up function map.
        self.action_map: dict[str, Action] = {}
        if actions:
            for action in actions:
                self.action_map[action.name] = action

        self.run_context_provider = run_context_provider

        # A help message can be generated for the function map.
        if with_help:
            self.action_map["help"] = Action(self.help)

        # This allows actions to be called as attributes.
        self.functions = ActionHandler(self)

    def help(self, run_context: RunContext) -> str:
        """Return a help message."""

        usage = [f"{action.usage()}" for action in self.action_map.values()]
        usage.sort()
        return "Actions:\n" + "\n".join(usage)

    def add_function(self, function: ActionCallable, name: str | None = None, description: str | None = None) -> None:
        """Register a function as an action."""
        if not name:
            name = function.__name__
        self.action_map[name] = Action(function, name, description)

    def add_functions(self, functions: list[ActionCallable]) -> None:
        """Register a list of functions as actions."""
        for function in functions:
            self.add_function(function)

    def has_action(self, name: str) -> bool:
        return name in self.action_map

    def get_action(self, name: str) -> Action | None:
        return self.action_map.get(name)

    def get_actions(self) -> list[Action]:
        return list(self.action_map.values())

    async def run_action_by_name(
        self,
        name: str,
        args: tuple = (),
        kwargs: dict[str, Any] = {},
    ) -> Any:
        """
        Run an action by name.
        """
        action = self.get_action(name)
        if not action:
            raise ValueError(f"Function {name} not found in registry.")

        run_context = self.run_context_provider.create_run_context()
        return await action.execute(run_context, *args, **kwargs)

    async def run_action_string(self, action_string: str) -> Any:
        """Parse an action string and execute the action. Used in running routines."""
        # TODO: If used in routines, need to handle skill namespacing (designations).
        action, args, kwargs = self.parse_action_string(action_string)
        if not action:
            raise ValueError("Action not found in registry.")
        run_context = self.run_context_provider.create_run_context()
        return await action.execute(run_context, *args, **kwargs)

    def parse_action_string(self, action_string: str) -> tuple[Action | None, list[Any], dict[str, Any]]:
        """Parse an action string into an action and its arguments."""

        # TODO: If used in routines, need to handle skill namespacing (designations).

        action_name, args, kwargs = parse_command_string(action_string)

        action = self.get_action(action_name)
        if not action:
            return None, [], {}

        return action, list(args), kwargs
