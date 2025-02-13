# skill_library/actions.py

import inspect
from dataclasses import dataclass
from typing import Any

from .types import ActionFn


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


def get_parameters(fn: ActionFn) -> list[Parameter]:
    parameters = dict(inspect.signature(fn).parameters)
    return [
        Parameter(
            name=param_name,
            type=param.annotation,
            description=None,  # param.annotation.description,
            default_value=param.default,
        )
        for param_name, param in parameters.items()
    ]


def get_action_usage(fn: ActionFn, name: str | None = None, description: str | None = None) -> Usage:
    """
    Get the usage string for a function.
    """
    name = name or fn.__name__
    description = description or inspect.getdoc(fn) or name.replace("_", " ").title()
    return Usage(name=name, parameters=get_parameters(fn), description=description)
