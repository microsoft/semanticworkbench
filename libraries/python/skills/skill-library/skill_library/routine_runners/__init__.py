from typing import Union

from .instruction_routine_runner import InstructionRoutineRunner
from .program_routine_runner import ProgramRoutineRunner

RunnerTypes = Union[InstructionRoutineRunner, ProgramRoutineRunner]

__all__ = ["InstructionRoutineRunner", "RunnerTypes"]
