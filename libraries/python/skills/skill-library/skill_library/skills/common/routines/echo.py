"""
web research skill
"""

from typing import Any

from skill_library import AskUserFn, EmitFn, RunContext, RunRoutineFn


async def main(
    context: RunContext,
    routine_state: dict[str, Any],
    emit: EmitFn,
    run: RunRoutineFn,
    ask_user: AskUserFn,
) -> str:
    await ask_user("What do you want to echo?")
    history = (await context.conversation_history()).messages
    message = history[-1].content
    return message
