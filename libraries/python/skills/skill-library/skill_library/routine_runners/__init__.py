from typing import Union

from .function_routine_runner import FunctionRoutineRunner
from .instruction_routine_runner import InstructionRoutineRunner
from .program_routine_runner import ProgramRoutineRunner

RunnerTypes = Union[InstructionRoutineRunner, ProgramRoutineRunner, FunctionRoutineRunner]

__all__ = ["InstructionRoutineRunner", "RunnerTypes"]
