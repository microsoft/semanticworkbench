from typing import Union

from .instruction_routine_runner import InstructionRoutineRunner
from .program_routine_runner import ProgramRoutineRunner
from .state_machine_routine_runner import StateMachineRoutineRunner

RunnerTypes = Union[InstructionRoutineRunner, ProgramRoutineRunner, StateMachineRoutineRunner]

__all__ = ["InstructionRoutineRunner", "RunnerTypes"]
