from typing import TYPE_CHECKING, Any, Awaitable, Callable

from events import BaseEvent, InformationEvent

if TYPE_CHECKING:
    pass

from ..routine import InstructionRoutine
from ..run_context import RunContext
from ..utilities import find_template_vars, make_arg_set

RespondFunction = Callable[[str], Awaitable[BaseEvent]]


class InstructionRoutineRunner:
    def __init__(self, respond_function: RespondFunction) -> None:
        self.respond = respond_function

    async def run(
        self, context: RunContext, routine: InstructionRoutine, *args: Any, **kwargs: Any
    ) -> tuple[bool, Any]:
        """
        Run an Instruction routine. This just runs through the steps of a
        routine, sending each one to its skill's response endpoint.

        Note, this means this can only be used with skills that have been
        configured with a chat driver, and this currently doesn't work in a
        "cross-skill" way. All actions must be accessible from the chat driver
        of the skill that packages the routine. This is of limited use, but this
        was the first routine runner we built as a demo and it may have some
        utility in edge cases.

        This could be much more sophisticated, though. In addition to making it
        cross-skill, it might handle more configuration, manage results of
        steps, handle errors and retries, add meta-cognitive functions, tracking
        progress and changing steps as necessary. Probably better to invest all
        of these ideas in other routine runners, though.
        """

        # Make kwargs out of args (aligning them to the order of the mustache
        # variables in the routine).
        arg_set = make_arg_set(find_template_vars(routine.routine), args, kwargs)

        # Replace mustache variables in the routine with the values from the arg set.
        parsed_routine = routine.routine
        for key, value in arg_set.items():
            parsed_routine = parsed_routine.replace(f"{{{{ {key} }}}}", str(value))
            parsed_routine = parsed_routine.replace(f"{{{{{key}}}}}", str(value))

        # Detect if there are any un-replaced mustache variables in the routine.
        if find_template_vars(parsed_routine):
            context.emit(
                InformationEvent(
                    message=f"Unresolved mustache variables in routine. You need more keyword args: {', '.join(find_template_vars(parsed_routine))}"
                )
            )
            return True, None

        # TODO: save a copy of this routine to run state.

        steps = [step.strip() for step in parsed_routine.split("\n") if step.strip()]
        for step in steps:
            context.emit(InformationEvent(message=f"Running step: {step}"))
            response: BaseEvent = await self.respond(step)
            informationEvent = InformationEvent(**response.model_dump())
            context.emit(informationEvent)

        return True, None

    async def next(self, context: RunContext, routine: InstructionRoutine, message: str) -> tuple[bool, Any]:
        """
        Run the next step in the current routine.
        """

        # Instruction routines have no "next" step as the entire routine is run
        # in one go. If we have gotten into this state (because of an error
        # while running the routine, and the stack wasn't popped) then go ahead
        # and finish to clear the state.
        informationEvent = InformationEvent(
            message="Instruction routine was previously run and ended without clearing the stack state. Clearing now. Try running the routine again."
        )
        context.emit(informationEvent)
        return True, None
