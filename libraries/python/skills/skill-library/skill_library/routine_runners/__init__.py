from typing import Union

from .action_list_routine_runner import ActionListRoutineRunner
from .instruction_routine_runner import InstructionRoutineRunner
from .program.runner import ProgramRoutineRunner
from .state_machine_routine_runner import StateMachineRoutineRunner

RunnerTypes = Union[ActionListRoutineRunner, InstructionRoutineRunner, ProgramRoutineRunner, StateMachineRoutineRunner]

__all__ = [
    "ActionListRoutineRunner",
    "InstructionRoutineRunner",
    "ProgramRoutineRunner",
    "RunnerTypes",
    "StateMachineRoutineRunner",
]
