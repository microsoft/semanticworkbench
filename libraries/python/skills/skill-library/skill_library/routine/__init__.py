from typing import Union

from .action_list_routine import ActionListRoutine
from .instruction_routine import InstructionRoutine
from .program_routine import ProgramRoutine
from .routine import Routine
from .state_machine_routine import StateMachineRoutine

RoutineTypes = Union[ActionListRoutine, InstructionRoutine, ProgramRoutine, StateMachineRoutine]

__all__ = [
    "ActionListRoutine",
    "InstructionRoutine",
    "ProgramRoutine",
    "StateMachineRoutine",
    "Routine",
    "RoutineTypes",
]
