from typing import TYPE_CHECKING, Any, Awaitable, Callable

from events import BaseEvent, InformationEvent, NoticeEvent

if TYPE_CHECKING:
    pass

from ..routine import ActionListRoutine
from ..run_context import RunContext
from ..utilities import find_template_vars, make_arg_set, parse_command_string, parse_template, to_string

RespondFunction = Callable[[str], Awaitable[BaseEvent]]


class ActionListRoutineRunner:
    async def run(
        self, run_context: RunContext, routine: ActionListRoutine, *args: Any, **kwargs: Any
    ) -> tuple[bool, Any]:
        """
        Run an Action List routine. This just runs through the steps of a
        routine, which should be actions, and executes each one. Note: It might
        handle more configuration, manage results of steps, handle errors and
        retries, etc. Also, we might add meta-cognitive functions, tracking
        progress and changing steps as necessary.
        """

        # Make kwargs out of args (aligning them to the order of the mustache
        # variables in the routine).
        arg_set = make_arg_set(find_template_vars(routine.routine), args, kwargs)

        # Validate the routine.
        try:
            routine.validate(arg_set)
        except ValueError as e:
            run_context.emit(InformationEvent(message=f"Routine failed validation. {e}"))
            return True, None

        # Replace mustache variables in the routine with the values from the arg
        # set.
        parsed_routine = parse_template(routine.routine, arg_set)

        # Get current step and locals from the stack frame state.
        async with run_context.stack_frame_state() as state:
            state["routine"] = parsed_routine
            current_step = state.get("current_step", 0)
            locals = state.get("locals", arg_set)
            state["current_step"] = current_step
            state["locals"] = locals

        await self.next(run_context, routine, "")

        return True, None

    async def next(self, run_context: RunContext, routine: ActionListRoutine, message: str) -> tuple[bool, Any]:
        """
        Run the next step in the current routine.
        """

        # Reload state
        async with run_context.stack_frame_state() as state:
            parsed_routine: str = state["routine"]
            current_step: int = state["current_step"]

        # Run the remaining steps.
        lines = [line.strip() for line in parsed_routine.split("\n") if line.strip()]
        for line in lines[current_step:]:
            async with run_context.stack_frame_state() as state:
                run_context.emit(InformationEvent(message=f"Running step: {line}"))

                # Separate output variables from the action string.
                output_variable_name, command_string = line.split(":", 1)

                # Replace mustache variables in the command string with locals.
                command_string = parse_template(command_string, state["locals"]).strip()

                # Parse the command string into a command and args.
                command, args, kwargs = parse_command_string(command_string)

                # Run the action!
                match command:
                    case "run_routine":
                        # TODO: This is untested.
                        result: Any = await run_context.run_routine(command, *args, **kwargs)
                    case "print":
                        run_context.emit(InformationEvent(message=args[0]))
                        result = None
                    case _:
                        result: Any = await run_context.run_action(command, *args, **kwargs)

                # Save and report on the result.
                result_string = to_string(result)
                state["locals"][output_variable_name] = result_string
                run_context.emit(NoticeEvent(message=result_string))

                # Increment the current step.
                current_step += 1
                state["current_step"] = current_step

        return True, None
