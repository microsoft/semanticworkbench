"""Program runner interface.

This module contains the high-level interface for program execution and
the abstract base class for execution environments.
"""

from typing import Any

from events import InformationEvent, MessageEvent
from semantic_workbench_api_model.workbench_model import ConversationMessageList

from skill_library.routine.program_routine import ProgramRoutine
from skill_library.run_context import RunContext
from skill_library.utilities import find_template_vars, make_arg_set, parse_template

from .interpreter import Interpreter
from .types import PausedExecution, ReturnValue


class ProgramRoutineLogger:
    def __init__(self, run_context: RunContext) -> None:
        self.run_context = run_context

    def log(self, message: str) -> None:
        self.run_context.emit(InformationEvent(message=message))


class ProgramRoutineRunner:
    """High-level interface for program execution.

    Coordinates between interpreter and execution environment,
    managing program lifecycle and external function calls.

    Attributes:
        context: Execution environment context
        interpreter: Program interpreter instance

    Requirements:
        - Must handle program lifecycle
        - Must coordinate external calls
        - Must maintain program state
        - Must provide clear results
    """

    async def start(
        self, run_context: RunContext, routine: ProgramRoutine, *args: Any, **kwargs: Any
    ) -> tuple[bool, Any]:
        """Start program execution."""

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
        try:
            parsed_program = parse_template(routine.program, arg_set)
            log_func = ProgramRoutineLogger(run_context).log
            interpreter = Interpreter(log_func).load_code(parsed_program)
        except Exception as e:
            run_context.emit(InformationEvent(message=f"Failed to parse routine. {e}"))
            return True, None

        async with run_context.stack_frame_state() as state:
            state["program_state"] = interpreter.get_state()

        return await self._execute(run_context, interpreter)

    async def resume(self, run_context: RunContext, message: str | None) -> tuple[bool, Any]:
        """Resume with external function result."""
        async with run_context.stack_frame_state() as state:
            program_state: str = state["program_state"]
            log_func = ProgramRoutineLogger(run_context).log
            interpreter = Interpreter.from_state(program_state, log_func)

            # Let the interpreter know the result of the last-paused function if
            # we're waiting for one. Currently, this is just used for "ask_user".
            if "paused_function_name" in state:
                func_name = state["paused_function_name"]
                cache_key = state["paused_function_cache_key"]
                interpreter.add_function_result(func_name, cache_key, message)
                del state["paused_function_name"]
                del state["paused_function_cache_key"]

        return await self._execute(run_context, interpreter)

    async def _execute(self, run_context: RunContext, interpreter: Interpreter) -> tuple[bool, Any]:
        run_context.emit(InformationEvent(message="Running Program routine."))
        gen = interpreter.execute_with_pausing()

        while True:
            status = next(gen)
            if status is None:
                # No return at the end of the program.
                return True, None
            if isinstance(status, PausedExecution):
                match status.func_name:
                    case "run_routine":
                        # TODO: This is untested. Ideally, it should result in a
                        # new stack frame and the execution of the routine with
                        # all messages being routed to it's "resume" methods.
                        result: Any = await run_context.run_routine(status.func_name, *status.args, **status.kwargs)
                    case "print":
                        run_context.emit(InformationEvent(message=status.args[0]))
                        result = None
                        interpreter.add_function_result("print", status.cache_key, result)
                    case "ask_user":
                        run_context.emit(MessageEvent(message=status.args[0]))

                        # Save state and pause execution in wait for a message.
                        async with run_context.stack_frame_state() as state:
                            state["program_state"] = interpreter.get_state()
                            state["paused_function_name"] = status.func_name
                            state["paused_function_cache_key"] = status.cache_key

                        return False, None
                    case "last_message":
                        # Get the last message from the conversation history.
                        messages: ConversationMessageList = await run_context.conversation_history()
                        if messages.messages:
                            result = messages.messages[-1].content
                        else:
                            result = None
                    case _:
                        # Actions don't need to be able to "ask user" so we
                        # don't need to cache the result. We can just run the
                        # action and its result to our interpreter cache.
                        result = await run_context.run_action(status.func_name, *status.args, **status.kwargs)
                        interpreter.add_function_result(status.func_name, status.cache_key, result)

                async with run_context.stack_frame_state() as state:
                    state["program_state"] = interpreter.get_state()

            elif isinstance(status, ReturnValue):
                return True, status.value

            else:
                run_context.emit(InformationEvent(message="Unexpected return value from program."))
                return True, None
