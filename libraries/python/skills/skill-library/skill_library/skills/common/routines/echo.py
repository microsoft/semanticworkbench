"""
web research skill
"""

from skill_library import RunContext
from skill_library.types import AskUserFn, EmitFn, GetStateFn, RunRoutineFn, SetStateFn


# Define your routine function. We could use a string here, but it's better to
# use a function and then get the source code of that function so we can lint
# it.
async def main(
    context: RunContext,
    ask_user: AskUserFn,
    run: RunRoutineFn,
    get_state: GetStateFn,
    set_state: SetStateFn,
    emit: EmitFn,
) -> str:
    await ask_user("What do you want to echo?")
    history = (await context.conversation_history()).messages
    message = history[-1].content
    print(f"Echoing: {message}")
    return message
