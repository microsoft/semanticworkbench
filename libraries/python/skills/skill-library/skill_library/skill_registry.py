import importlib
import os
from typing import Any

from .routine import FunctionRoutine, InstructionRoutine, ProgramRoutine, RoutineTypes
from .routine_runners import FunctionRoutineRunner, InstructionRoutineRunner, ProgramRoutineRunner
from .run_context import RunContext
from .skill import Skill


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

    def get_routine(self, routine_name: str) -> RoutineTypes | None:
        """
        Get a routine by name.
        """
        skill_name, routine = routine_name.split(".")
        skill = self.get_skill(skill_name)
        if not skill:
            return None
        return skill.get_routine(routine)

    async def run_routine_by_name(
        self, context: RunContext, name: str, vars: dict[str, Any] | None = None
    ) -> Any:
        """
        Run an assistant routine by name (<skill_name>.<routine_name>).
        """
        routine = self.get_routine(name)
        if not routine:
            raise ValueError(f"Routine {name} not found.")
        response = await self.run_routine(context, routine, vars)
        return response

    async def run_routine(
        self, context: RunContext, routine: RoutineTypes, vars: dict[str, Any] | None = None
    ) -> Any:
        """
        Run an assistant routine. This is going to be much of the
        magic of the assistant. Currently, is just runs through the
        steps of a routine, but this will get much more sophisticated.
        It will need to handle configuration, managing results of steps,
        handling errors and retries, etc. ALso, this is where we will put
        meta-cognitive functions such as having the assistant create a plan
        from the routine and executing it dynamically while monitoring progress.
        name = <skill_name>.<routine_name>
        """
        await context.routine_stack.push(routine.fullname())
        match routine:
            case InstructionRoutine():
                runner = InstructionRoutineRunner()
                done = await runner.run(context, routine, vars)
            case ProgramRoutine():
                runner = ProgramRoutineRunner()
                done = await runner.run(context, routine, vars)
            case FunctionRoutine():
                runner = FunctionRoutineRunner()
                done = await runner.run(context, routine, vars)
        if done:
            _ = await context.routine_stack.pop()

    async def step_active_routine(self, context: RunContext, message: str) -> None:
        """Run another step in the current routine."""
        routine_frame = await context.routine_stack.peek()
        if not routine_frame:
            raise ValueError("No routine to run.")

        routine = self.get_routine(routine_frame.name)
        if not routine:
            raise ValueError(f"Routine {routine_frame.name} not found.")

        match routine:
            case InstructionRoutine():
                runner = InstructionRoutineRunner()
                done = await runner.next(context, routine, message)
            case ProgramRoutine():
                runner = ProgramRoutineRunner()
                done = await runner.next(context, routine, message)
            case FunctionRoutine():
                runner = FunctionRoutineRunner()
                done = await runner.next(context, routine, message)

        if done:
            await context.routine_stack.pop()
            # TODO: Manage return state for composition in parent steps.


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
