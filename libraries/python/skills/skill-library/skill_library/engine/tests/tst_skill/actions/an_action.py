# tst_skill/actions/an_action.py
from skill_library.engine.run_context import RunContext


async def main(context: RunContext) -> str:
    skill = context.tst_skill.skill
    skill.call_count += 1
    return "action called"
