# tst_skill/actions/an_action.py
from skill_library import RunContext

from tst_skill import TstSkill


async def increment(context: RunContext) -> str:
    skill = context.skills["tst_skill"]
    if isinstance(skill, TstSkill):
        skill.call_count += 1
    return "action called"


__default__ = increment
