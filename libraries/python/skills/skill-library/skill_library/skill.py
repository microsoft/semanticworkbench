# skill_library/skill.py

import importlib
import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel

from .logging import logger
from .types import ActionFn, RoutineFn


class SkillConfig(BaseModel):
    """Base configuration that all skill configs inherit from"""

    name: str

    class Config:
        arbitrary_types_allowed = True


class SkillProtocol(Protocol):
    """Base protocol that all skills must implement"""

    config: SkillConfig
    _actions: dict[str, ActionFn]
    _routines: dict[str, RoutineFn]


class Skill:
    def __init__(self, config: SkillConfig):
        self.config = config
        self._actions: dict[str, ActionFn] = {}
        self._routines: dict[str, RoutineFn] = {}

        # Auto-discover and register actions and routines
        module = sys.modules[self.__class__.__module__]
        package_name = module.__package__ or module.__name__
        logger.info(f"Discovering skills in package: {package_name}")

        # For library skills, we can use the module's __file__ attribute
        module_file = getattr(module, "__file__", None)
        if module_file is not None:
            package_path = Path(module_file).parent
        else:
            # Fallback to find_spec for other cases
            spec = importlib.util.find_spec(package_name)
            if not spec or not spec.origin:
                raise ValueError(f"Could not find package path for {package_name}")
            package_path = Path(spec.origin).parent

        # Look for actions (using __default__)
        actions_path = package_path / "actions"
        if actions_path.exists():
            for file in actions_path.glob("*.py"):
                if file.name == "__init__.py":
                    continue
                action_name = file.stem
                action_module = importlib.import_module(f"{package_name}.actions.{action_name}")

                if hasattr(action_module, "__default__"):
                    action = action_module.__default__
                    if callable(action) and inspect.iscoroutinefunction(action):
                        self.register_action(action_name, action)
                        continue
                    else:
                        raise ValueError(f"Action {action_name} '__default__' is not a coroutine function")

                raise ValueError(f"Action module {action_name} must have a '__default__' coroutine function export")
        else:
            raise (ValueError(f"No actions directory found in {package_path}"))

        # Look for routines
        routines_path = package_path / "routines"
        if routines_path.exists():
            for file in routines_path.glob("*.py"):
                if file.name == "__init__.py":
                    continue
                routine_name = file.stem
                routine_module = importlib.import_module(f"{package_name}.routines.{routine_name}")

                if hasattr(routine_module, "main"):
                    routine = routine_module.main
                    if isinstance(routine, RoutineFn):
                        self.register_routine(routine_name, routine)
                        continue
                    else:
                        routine_function_attrs = [attr for attr in dir(RoutineFn) if not attr.startswith("_")]
                        routine_attrs = [attr for attr in dir(routine) if not attr.startswith("_")]
                        raise ValueError(
                            f"Routine {routine_name} 'main' is not a RoutineFn. Expected attributes: {routine_function_attrs}, Found: {routine_attrs}"
                        )

                raise ValueError(f"Routine module {routine_name} must have a 'main' coroutine function")

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
