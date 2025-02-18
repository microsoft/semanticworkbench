# skill_library/routine_info.py

import inspect
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, cast

if TYPE_CHECKING:
    from .skill import RoutineFn, Skill

# Standard routine parameters we want to skip in documentation
STANDARD_PARAMS = {"context", "ask_user", "run", "routine_state", "emit"}


def format_type(type_hint: Any) -> str:
    """Format type hints into readable strings"""
    import typing
    from typing import _GenericAlias  # type: ignore

    # If it's a string representation of a type, clean it up
    if isinstance(type_hint, str):
        return type_hint.replace("typing.", "")

    # Handle built-in types
    if isinstance(type_hint, type):
        return type_hint.__name__

    # Handle typing._GenericAlias (like list[str])
    if isinstance(type_hint, _GenericAlias):
        origin = typing.get_origin(type_hint)
        args = typing.get_args(type_hint)

        if origin == typing.Union:
            if type(None) in args:
                # Get the non-None type
                real_type = next(arg for arg in args if arg is not type(None))
                return f"Optional[{format_type(real_type)}]"
            return " | ".join(format_type(arg) for arg in args)

        if origin:
            formatted_args = [format_type(arg) for arg in args]
            origin_name = origin.__name__ if hasattr(origin, "__name__") else str(origin)
            return f"{origin_name}[{', '.join(formatted_args)}]"

    # If we get here, just convert to string and clean it up
    type_str = str(type_hint)
    return type_str.replace("typing.", "").replace("NoneType", "None").replace("ForwardRef(", "").replace(")", "")


@dataclass
class Parameter:
    """Describes a single parameter of a routine"""

    name: str
    type: Any
    description: str | None
    default_value: Any | None = None

    def __str__(self) -> str:
        param_type = format_type(self.type)
        usage = f"{self.name}: {param_type}"

        if self.default_value is not inspect.Parameter.empty:
            if isinstance(self.default_value, str):
                usage += f' = "{self.default_value}"'
            else:
                usage += f" = {self.default_value}"
        return usage


@dataclass
class RoutineUsage:
    """Documentation for a routine, including its parameters"""

    name: str
    parameters: list[Parameter]
    description: str

    def __str__(self) -> str:
        param_usage = ", ".join(str(param) for param in self.parameters)
        usage = f"__{self.name}__"
        if self.parameters:
            usage += f"\n    Parameters: ({param_usage})"
        if self.description:
            usage += f"\n    {self.description}"
        return usage

    def to_markdown(self) -> str:
        """Convert the routine usage to a markdown string"""
        routine = f"__{self.name}__"
        if self.parameters:
            param_usage = ", ".join(str(param) for param in self.parameters)
            routine += f"({param_usage})"

        description = None
        if self.description:
            # Clean description for markdown.

            # Split into lines and remove empty lines at start/end
            lines = [line.strip() for line in self.description.splitlines()]
            lines = [line for line in lines if line]

            # Join all lines with a space between them
            clean_doc = " ".join(lines)

            # Escape any markdown characters
            clean_doc = (
                clean_doc.replace("_", "\\_")  # Escape underscores
                .replace("*", "\\*")  # Escape asterisks
                .replace("`", "\\`")  # Escape backticks
                .replace("[", "\\[")  # Escape square brackets
                .replace("]", "\\]")
            )

            description = f"_{clean_doc}_"

        if description:
            return f"{routine}: {description}"
        else:
            return routine


def get_routine_parameters(fn: "RoutineFn") -> list[Parameter]:
    """Extract parameter information from a routine, excluding standard parameters"""
    # Cast to Callable to access function attributes
    func = cast(Callable, fn)
    parameters = dict(inspect.signature(func).parameters)
    return [
        Parameter(
            name=param_name,
            type=param.annotation,
            description=None,
            default_value=param.default,
        )
        for param_name, param in parameters.items()
        if param_name not in STANDARD_PARAMS
    ]


def get_routine_usage(fn: "RoutineFn", name: str | None = None) -> RoutineUsage:
    """Get the usage documentation for a routine"""
    func = cast(Callable, fn)
    routine_name = name if name is not None else getattr(func, "__name__", "unnamed_routine")
    routine_description = inspect.getdoc(func) or ""
    return RoutineUsage(name=routine_name, parameters=get_routine_parameters(fn), description=routine_description)


def routines_usage(skills: dict[str, "Skill"]) -> str:
    routines: list[str] = []
    for skill_name, skill in skills.items():
        for routine_name in skill.list_routines():
            routine = skill.get_routine(routine_name)
            if not routine:
                continue
            usage = get_routine_usage(routine, f"{skill_name}.{routine_name}")
            routines.append(f"- {usage.to_markdown()}")
    return "\n".join(routines)
