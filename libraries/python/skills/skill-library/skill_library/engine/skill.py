import importlib
import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Any, Generic, Protocol, TypeVar

from pydantic import BaseModel

from .run_context import RunContext
from .types import ActionFn, RoutineFn


class SkillConfig(BaseModel):
    """Base configuration that all skill configs inherit from"""

    skill_name: str


class SkillProtocol(Protocol):
    """Base protocol that all skills must implement"""

    config: SkillConfig
    _actions: dict[str, ActionFn]
    _routines: dict[str, RoutineFn]


T = TypeVar("T", bound=SkillProtocol)


class BoundSkill(Generic[T]):
    """A skill that's been bound to a specific run context"""

    def __init__(self, skill: T, context: "RunContext"):
        self.skill = skill
        self.context = context

    def __getattr__(self, name: str):
        # First try to get from _actions
        if name in self.skill._actions:
            action = self.skill._actions[name]

            async def bound_action(*args: Any, **kwargs: Any) -> Any:
                return await action(self.context, *args, **kwargs)

            return bound_action

        # Then try normal attribute accesss.
        try:
            attr = getattr(self.skill, name)
            if callable(attr):
                if inspect.iscoroutinefunction(attr):

                    async def bound_async_fn(*args: Any, **kwargs: Any) -> Any:
                        return await attr(self.context, *args, **kwargs)

                    return bound_async_fn
                else:

                    def bound_fn(*args: Any, **kwargs: Any) -> Any:
                        return attr(self.context, *args, **kwargs)

                    return bound_fn
            return attr
        except AttributeError:
            raise AttributeError(f"Attribute {name} not found on skill {self.skill.config.skill_name}")


class Skill:
    def __init__(self, config: SkillConfig):
        self.config = config
        self._actions: dict[str, ActionFn] = {}
        self._routines: dict[str, RoutineFn] = {}

        # Auto-discover and register actions and routines
        module = sys.modules[self.__class__.__module__]
        package_name = module.__package__ or module.__name__
        print(f"Discovering skills in package: {package_name}")

        try:
            # Get the module's location
            spec = importlib.util.find_spec(package_name)
            if not spec or not spec.origin:
                raise ValueError(f"Could not find package path for {package_name}")

            package_path = Path(spec.origin).parent
            print(f"Package path: {package_path}")

            # Look for actions
            actions_path = package_path / "actions"
            print(f"Looking for actions in: {actions_path}")
            if actions_path.exists():
                for file in actions_path.glob("*.py"):
                    if file.name == "__init__.py":
                        continue
                    print(f"Found action file: {file.name}")
                    action_name = file.stem
                    action_module = importlib.import_module(f"{package_name}.actions.{action_name}")
                    if hasattr(action_module, "main"):
                        action = getattr(action_module, "main")
                        if callable(action) and inspect.iscoroutinefunction(action):
                            print(f"Registering action: {action_name}")
                            self.register_action(action_name, action)

            # Look for routines
            routines_path = package_path / "routines"
            print(f"Looking for routines in: {routines_path}")
            if routines_path.exists():
                for file in routines_path.glob("*.py"):
                    if file.name == "__init__.py":
                        continue
                    print(f"Found routine file: {file.name}")
                    routine_name = file.stem
                    routine_module = importlib.import_module(f"{package_name}.routines.{routine_name}")
                    if hasattr(routine_module, "main"):
                        routine = getattr(routine_module, "main")
                        if callable(routine) and inspect.iscoroutinefunction(routine):
                            print(f"Registering routine: {routine_name}")
                            self.register_routine(routine_name, routine)

        except Exception as e:
            print(f"Error discovering modules: {e}")

    def register_action(self, name: str, fn: ActionFn):
        self._actions[name] = fn

    def register_routine(self, name: str, fn: RoutineFn):
        self._routines[name] = fn

    def get_action(self, name: str) -> ActionFn | None:
        return self._actions.get(name)

    def get_routine(self, name: str) -> RoutineFn | None:
        return self._routines.get(name)

    def list_actions(self) -> list[str]:
        """Return list of available action names"""
        return list(self._actions.keys())

    def list_routines(self) -> list[str]:
        """Return list of available routine names"""
        return list(self._routines.keys())

    def bind_context(self, context: RunContext) -> BoundSkill:
        """Bind this skill to a specific run context"""
        return BoundSkill(self, context)
