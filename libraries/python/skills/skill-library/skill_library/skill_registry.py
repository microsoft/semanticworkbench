from .routine import RoutineTypes
from .skill import Skill
import os
import importlib
from typing import Any


class SkillRegistry:
    """
    A skill registry is a collection of skills that an agent uses. When a skill
    is added, its dependencies are also added. This allows an agent to have a
    subset of the global skill registry.
    """

    def __init__(self, skills: list[Skill] = []) -> None:
        # self.global_skill_registry = GlobalSkillRegistry()
        self.required_skills = []
        self.registered_skills: dict[str, Skill] = {}
        self.register_all_skills(skills)

    def register_all_skills(self, skills: list[Skill]) -> None:
        """
        Register all skills and their dependencies.
        """

        # Topological sort of skills to ensure that dependencies are registered
        # first.
        sorted_skills: list[Skill] = []

        def walk_skill(skill: Skill) -> None:
            if skill.name in sorted_skills:
                return
            for dependency in skill.dependencies:
                if dependency not in [skill.name for skill in self.required_skills]:
                    raise ValueError(f"Dependency {dependency} not found in global skill registry.")

                for required_skill in self.required_skills:
                    if required_skill.name == dependency:
                        walk_skill(required_skill)
                        break

            sorted_skills.append(skill)

        for skill in skills:
            walk_skill(skill)

        # Register the sorted skills.
        for skill in sorted_skills:
            self.registered_skills[skill.name] = skill

    def get_skill(self, skill_name) -> Skill | None:
        return self.registered_skills[skill_name]

    def get_skills(self) -> list[Skill]:
        return list(self.registered_skills.values())

    def list_actions(self) -> list[str]:
        """
        List all namespaced function names available in the skill registry.
        """
        actions = []
        for skill in self.get_skills():
            actions += [f"{skill.name}.{action}" for action in skill.list_actions()]
        return actions

    def list_routines(self) -> list[str]:
        """
        List all namespaced routine names available in the skill registry.
        """
        routines = []
        for skill in self.get_skills():
            routines += [f"{skill.name}.{routine}" for routine in skill.list_routines()]
        return routines

    def has_routine(self, routine_name: str) -> bool:
        """
        Check if a routine exists in the skill registry.
        """
        skill_name, routine = routine_name.split(".")
        skill = self.get_skill(skill_name)
        if not skill:
            return False
        return skill.has_routine(routine)

    def get_routine(self, routine_name: str) -> tuple[Skill | None, RoutineTypes | None]:
        """
        Get a routine by name.
        """
        skill_name, routine = routine_name.split(".")
        skill = self.get_skill(skill_name)
        if not skill:
            return None, None
        return skill, skill.get_routine(routine)


SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
SKILLS_DIR = os.path.join(SCRIPT_DIR, "skills")


class GlobalSkillRegistry:
    """
    A global skill registry is a collection of all skills that an agent can
    use. All skills in the skills directory are registered in the global skill
    registry. Custom skills can be added to the skills directory.
    """

    def __init__(self):
        self.skills = {}

        # Register all skills in the skills directory.
        for skill_name in os.listdir(SKILLS_DIR):
            skill_module = importlib.import_module(f".skills.{skill_name}")
            skill_class = getattr(skill_module, "CLASS_NAME" or skill_name.title() + "Skill")
            if not skill_class:
                raise ValueError(f"Skill class not found in skill module {skill_module}.")
            skill = skill_class()
            self.register_skill(skill)

    def register_skill(self, skill) -> None:
        self.skills[skill.name] = skill

    def get_skill(self, skill_name) -> Skill:
        return self.skills[skill_name]

    def get_skills(self) -> dict[Any, Any]:
        return self.skills

    def has_skill(self, skill_name) -> bool:
        return skill_name in self.skills
