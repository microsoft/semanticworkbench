from pathlib import Path
from typing import Any

from events import MessageEvent
from skill_library import AskUserFn, EmitFn, RunContext, RunRoutineFn


async def main(
    context: RunContext,
    routine_state: dict[str, Any],
    emit: EmitFn,
    run: RunRoutineFn,
    ask_user: AskUserFn,
    pattern: str,
) -> str:
    """Show a fabric patterns."""

    pattern_file = Path(__file__).parent.parent / "patterns" / pattern / "system.md"
    if not pattern_file.exists():
        emit(MessageEvent(message=f"Pattern {pattern} not found."))
        return f"Pattern {pattern} not found."

    with open(pattern_file, "r") as f:
        pattern = f.read()

    return f"```markdown\n{pattern}\n```"
