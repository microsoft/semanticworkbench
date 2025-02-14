# skill_library/skill.py

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel

from skill_library.types import AskUserFn, EmitFn, RunContext, RunRoutineFn

from .logging import extra_data, logger


@runtime_checkable
class RoutineFn(Protocol):
    async def __call__(
        self,
        context: RunContext,
        routine_state: dict[str, Any],
        emit: EmitFn,
        run: RunRoutineFn,
        ask_user: AskUserFn,
        *args: Any,
        **kwargs: Any,
    ) -> Any: ...


class SkillConfig(BaseModel):
    """Base configuration that all skill configs inherit from"""

    name: str

    class Config:
        arbitrary_types_allowed = True


class SkillProtocol(Protocol):
    """Base protocol that all skills must implement"""

    config: SkillConfig
    _routines: dict[str, RoutineFn]


class Skill:
    def __init__(self, config: SkillConfig):
        self.config = config
        self._routines: dict[str, RoutineFn] = {}

        # Auto-discover and register routines.
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

                logger.warning(
                    "Routine module skipped. Routine has no `main` function.",
                    extra_data({"routine_name": routine_name}),
                )

    def register_routine(self, name: str, fn: RoutineFn):
        self._routines[name] = fn

    def get_routine(self, name: str) -> RoutineFn | None:
        return self._routines.get(name)

    def list_routines(self) -> list[str]:
        """Return list of available routine names"""
        return list(self._routines.keys())
