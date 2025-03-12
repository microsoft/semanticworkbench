import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict

from .logging import extra_data, logger
from .types import AskUserFn, EmitFn, RunContext, RunRoutineFn


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

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )


class SkillProtocol(Protocol):
    """Base protocol that all skills must implement"""

    config: SkillConfig
    _routines: dict[str, RoutineFn]


class Skill:
    def __init__(self, config: SkillConfig):
        self.config = config
        self._routines: dict[str, RoutineFn] = {}
        self._package_path: Path | None = None
        self._package_name: str | None = None

        # Store package info during initialization
        module = sys.modules[self.__class__.__module__]
        self._package_name = module.__package__ or module.__name__
        logger.info(f"Discovering skills in package: {self._package_name}")

        # For library skills, we can use the module's __file__ attribute
        module_file = getattr(module, "__file__", None)
        if module_file is not None:
            self._package_path = Path(module_file).parent
        else:
            # Fallback to find_spec for other cases
            spec = importlib.util.find_spec(self._package_name)
            if not spec or not spec.origin:
                raise ValueError(f"Could not find package path for {self._package_name}")
            self._package_path = Path(spec.origin).parent

        # Initial load of routines
        self._load_routines()

    def _load_routines(self) -> None:
        """Load all routines from the routines directory"""
        if not self._package_path:
            raise ValueError("Package path not initialized")

        self._routines.clear()
        routines_path = self._package_path / "routines"

        if routines_path.exists():
            for file in routines_path.glob("*.py"):
                if file.name == "__init__.py":
                    continue
                routine_name = file.stem
                self._load_routine(routine_name)

    def _load_routine(self, routine_name: str) -> None:
        """Load a specific routine module"""
        if not self._package_name:
            raise ValueError("Package name not initialized")

        # Remove the old module if it exists
        module_name = f"{self._package_name}.routines.{routine_name}"
        if module_name in sys.modules:
            del sys.modules[module_name]

        try:
            # Import the module fresh
            routine_module = importlib.import_module(module_name)

            # Force reload to get latest changes
            importlib.reload(routine_module)

            if hasattr(routine_module, "main"):
                routine = routine_module.main
                if isinstance(routine, RoutineFn):
                    self.register_routine(routine_name, routine)
                else:
                    routine_function_attrs = [attr for attr in dir(RoutineFn) if not attr.startswith("_")]
                    routine_attrs = [attr for attr in dir(routine) if not attr.startswith("_")]
                    raise ValueError(
                        f"Routine {routine_name} 'main' is not a RoutineFn. "
                        f"Expected attributes: {routine_function_attrs}, Found: {routine_attrs}"
                    )
            else:
                logger.warning(
                    "Routine module skipped. Routine has no `main` function.",
                    extra_data({"routine_name": routine_name}),
                )
        except Exception as e:
            logger.error(
                f"Error loading routine {routine_name}: {str(e)}",
                extra_data({"routine_name": routine_name, "error": str(e)}),
            )
            raise

    def register_routine(self, name: str, fn: RoutineFn) -> None:
        self._routines[name] = fn

    def get_routine(self, name: str) -> RoutineFn | None:
        """Get a routine, reloading it first to ensure latest version"""
        if name in self._routines:
            self._load_routine(name)  # Reload the routine
        return self._routines.get(name)

    def list_routines(self) -> list[str]:
        """Return list of available routine names"""
        return list(self._routines.keys())

    # def list_attributes(self) -> list[str]:
    #     """List all available custom attributes in the skill"""

    #     attributes = [attr for attr in dir(self) if not attr.startswith("_") and callable(getattr(self, attr))]

    #     attrs = []

    #     # Get type annotations for each attribute
    #     for attr in attributes:
    #         attr_type = getattr(self, attr).__annotations__.get(attr)
    #         if attr_type:
    #             attrs.append(f"{attr}({format_type(attr_type)})")

    #     return attrs
