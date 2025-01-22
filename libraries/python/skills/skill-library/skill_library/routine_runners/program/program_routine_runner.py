import base64
import pickle
from typing import Any

from events import InformationEvent

from skill_library.utilities import find_template_vars, make_arg_set, parse_template

from ...routine import ProgramRoutine
from ...run_context import RunContext
from .interpreter import FunctionCall, Interpreter, InterpreterState, ReturnValue


class ProgramRoutineRunner:
    def __init__(self) -> None:
        pass

    async def run(
        self, run_context: RunContext, routine: ProgramRoutine, *args: Any, **kwargs: Any
    ) -> tuple[bool, Any]:
        """
        This implementation is not yet working. It is a placeholder for the
        future implementation of running a program routine. A program routine
        is a routine written in Python that can be executed by the assistant.
        The routine will refer to any skill.action(args) that it needs.
        """

        # Make kwargs out of args (aligning them to the order of the mustache
        # variables in the routine).
        arg_set = make_arg_set(find_template_vars(routine.program), args, kwargs)

        # Validate the routine.
        try:
            routine.validate(arg_set)
        except ValueError as e:
            run_context.emit(InformationEvent(message=f"Routine failed validation. {e}"))
            return True, None

        # Replace mustache variables in the routine with the values from the arg
        # set.
        parsed_program = parse_template(routine.program, arg_set)
        interpreter = Interpreter()
        interpreter.load_code(parsed_program)

        # Set interpreter state in stack frame.
        async with run_context.stack_frame_state() as state:
            state["program"] = parsed_program
            state["program_state"] = base64.b64encode(pickle.dumps(interpreter.get_state())).decode("utf-8")

        return await self.next(run_context, routine, "")

    async def next(self, run_context: RunContext, routine: ProgramRoutine, message: str) -> tuple[bool, Any]:
        """
        Run the next step in the current routine.
        """
        # Reload state
        async with run_context.stack_frame_state() as state:
            parsed_program: str = state["program"]
            program_state_str: str = state["program_state"]
            program_state: InterpreterState = pickle.loads(base64.b64decode(program_state_str.encode("utf-8")))

        interpreter = Interpreter()
        interpreter.load_code(parsed_program)
        interpreter.set_state(program_state)

        run_context.emit(InformationEvent(message="Running Program routine."))
        async with run_context.stack_frame_state() as state:
            next = interpreter.run()
            while next is not isinstance(next, ReturnValue):
                if isinstance(next, FunctionCall):
                    match next.func_name:
                        case "run_routine":
                            # TODO: This is untested.
                            result: Any = await run_context.run_routine(next.func_name, *next.args, **next.kwargs)
                        case "print":
                            run_context.emit(InformationEvent(message=next.args[0]))
                            result = None
                        case _:
                            result: Any = await run_context.run_action(next.func_name, *next.args, **next.kwargs)

                    result: Any = await run_context.run_action(next.func_name, *next.args, **next.kwargs)
                    state["program_state"] = base64.b64encode(pickle.dumps(interpreter.get_state())).decode("utf-8")

                    next = interpreter.run(result)

        return True, next
