from pathlib import Path
from typing import Any

from skill_library import AskUserFn, EmitFn, RunContext, RunRoutineFn


async def main(
    context: RunContext,
    routine_state: dict[str, Any],
    emit: EmitFn,
    run: RunRoutineFn,
    ask_user: AskUserFn,
) -> str:
    """List fabric patterns."""

    pattern_dir = Path(__file__).parent.parent / "patterns"
    dirs = [d.name for d in pattern_dir.iterdir() if d.is_dir()]
    patterns = "\n- ".join(dirs)
    return f"```markdown\n{patterns}\n```"
