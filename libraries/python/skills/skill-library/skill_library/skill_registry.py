import importlib
import os
from typing import Any

from skill_library.actions import Action

from .routine import InstructionRoutine, ProgramRoutine, RoutineTypes, StateMachineRoutine
from .routine_runners import InstructionRoutineRunner, ProgramRoutineRunner, StateMachineRoutineRunner
from .routine_stack import RoutineStack
from .run_context import RunContext, RunContextProvider
from .skill import Skill, SkillDefinition


class SkillRegistry:
    """
    A skill registry is a collection of skills that an assistant uses. When a
    skill is added, its dependencies are also added.
    """

    def __init__(
        self,
        skills: dict[str, SkillDefinition],
        run_context_provider: RunContextProvider,
        routine_stack: RoutineStack,
    ) -> None:
        # self.global_skill_registry = GlobalSkillRegistry()

        # Note: We give each skill a reference to the run context provider so
        # that it can optionally use it to create Chat Driver methods for a
        # natural language interface. This supports Instruction routines.
        self.skills = {
            skill_definition.name: skill_definition.skill_class(skill_definition, run_context_provider)
            for skill_definition in skills.values()
        }
        self.run_context_provider = run_context_provider
        self.routine_stack = routine_stack

    def get_skill(self, skill_name: str) -> Skill | None:
        return self.skills.get(skill_name)

    ######################################
    # Actions
    ######################################

    def list_actions(self, include_usage: bool = False) -> list[str]:
        """
        List all namespaced function names available in the skill registry.
        """
        actions = []
        for skill_name, skill in self.skills.items():
            for action in skill.action_registry.get_actions():
                if include_usage:
                    actions.append(f"{skill_name}.{action.usage()}")
                else:
                    actions.append(f"{skill_name}.{action.name}")

        return actions

    def get_action_by_designation(self, designation: str) -> Action | None:
        """
        Get a routine by <skill>.<routine> designation.
        """
        skill_name, action_name = designation.split(".")
        skill = self.get_skill(skill_name)
        if not skill:
            return None
        return skill.get_action(action_name)

    async def run_action_by_designation(self, run_context: RunContext, designation: str, *args, **kwargs) -> Any:
        """
        Run an action by designation (<skill_name>.<action_name>).
        """
        skill_name, action_name = designation.split(".")
        skill = self.get_skill(skill_name)
        if not skill:
            raise ValueError(f"Skill {skill_name} not found.")
        action = skill.get_action(action_name)
        if not action:
            raise ValueError(f"Action {action_name} not found in skill {skill_name}.")
        response = await action.execute(run_context, *args, **kwargs)
        return response

    ######################################
    # Routines
    ######################################

    def list_routines(self) -> list[str]:
        """
        List all namespaced routine names available in the skill registry.
        """
        routines = []
        for skill_name, skill in self.skills.items():
            routines += [f"{skill_name}.{routine}" for routine in skill.list_routines()]
        return routines

    def has_routine(self, designation: str) -> bool:
        """
        Check if a routine exists in the skill registry.
        """
        skill_name, routine = designation.split(".")
        skill = self.get_skill(skill_name)
        if not skill:
            return False
        return skill.has_routine(routine)

    def get_routine_by_designation(self, designation: str) -> RoutineTypes | None:
        """
        Get a routine by <skill>.<routine> designation.
        """
        skill_name, routine_name = designation.split(".")
        skill = self.get_skill(skill_name)
        if not skill:
            return None
        return skill.get_routine(routine_name)

    async def run_routine_by_designation(self, run_context: RunContext, designation: str, *args, **kwargs) -> Any:
        """
        Run an assistant routine by designation (<skill_name>.<routine_name>).
        """
        routine = self.get_routine_by_designation(designation)
        if not routine:
            raise ValueError(f"Routine {designation} not found.")
        response = await self.run_routine(run_context, routine, *args, **kwargs)
        return response

    async def run_routine(self, run_context: RunContext, routine: RoutineTypes, *args, **kwargs) -> Any:
        """
        Run an assistant routine. This is going to be much of the magic of the
        assistant. Currently, is just runs through the steps of a routine, but
        this will get much more sophisticated. It will need to handle
        configuration, managing results of steps, handling errors and retries,
        etc. ALso, this is where we will put meta-cognitive functions such as
        having the assistant create a plan from the routine and executing it
        dynamically while monitoring progress. name =
        <skill_name>.<routine_name>
        """

        # TODO: Different types of routines have different run signature
        # behavior. For example, the instruction routine needs template vars
        # passed in and that's probably all. The state machine routine, otoh,
        # needs to be initialized and then stepped through and the functions
        # need arg/kwarg parameters.

        # We'll need a way to map the args/kwargs to the run_routine function
        # signature so a user can get help/usage and the assistant routine
        # builder knows how to use them.

        await self.routine_stack.push(routine.fullname())
        match routine:
            case InstructionRoutine():
                skill = self.get_skill(routine.skill_name)
                if not skill:
                    raise ValueError(f"Skill {routine.skill_name} not found.")
                if skill.chat_driver is None:
                    raise ValueError(f"Skill {skill.name} needs a chat driver to run an instruction routine.")
                respond_function = skill.respond
                runner = InstructionRoutineRunner(respond_function)
                done, output = await runner.run(run_context, routine, *args, **kwargs)
            case ProgramRoutine():
                runner = ProgramRoutineRunner()
                done, output = await runner.run(run_context, routine, *args, **kwargs)
            case StateMachineRoutine():
                runner = StateMachineRoutineRunner()
                done, output = await runner.run(run_context, routine, *args, **kwargs)
            case _:
                raise ValueError(f"Routine type {type(routine)} not supported.")
        if done:
            _ = await self.routine_stack.pop()
            return output

    async def step_active_routine(self, run_context: RunContext, message: str) -> None:
        """Run another step in the current routine."""
        routine_frame = await self.routine_stack.peek()
        if not routine_frame:
            raise ValueError("No routine to run.")

        routine = self.get_routine_by_designation(routine_frame.name)
        if not routine:
            raise ValueError(f"Routine {routine_frame.name} not found.")

        match routine:
            case InstructionRoutine():
                # Instruction routines work by passing each line of the routine
                # to to the routine's skill's response function. This means any
                # skill that has an instruction routine needs to have a chat
                # driver.
                skill = self.get_skill(routine.skill_name)
                if not skill:
                    raise ValueError(f"Skill {routine.skill_name} not found.")
                if skill.chat_driver is None:
                    raise ValueError(f"Skill {skill.name} needs a chat driver to run an instruction routine.")
                respond_function = skill.respond
                runner = InstructionRoutineRunner(respond_function)
                done, output = await runner.next(run_context, routine, message)
            case ProgramRoutine():
                runner = ProgramRoutineRunner()
                done, output = await runner.next(run_context, routine, message)
            case StateMachineRoutine():
                runner = StateMachineRoutineRunner()
                done, output = await runner.next(run_context, routine, message)

        if done:
            await self.routine_stack.pop()
            return output


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
