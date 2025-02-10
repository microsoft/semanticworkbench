from typing import Any, Awaitable, Callable

from skill_library.engine import AskUserFn, RunContext, Skill, SkillConfig

ActionFn = Callable[[RunContext], Awaitable[Any]]
RoutineFn = Callable[[RunContext, AskUserFn], Awaitable[Any]]


class CommonSkillConfig(SkillConfig):
    """Configuration for the common skill"""

    pass


class CommonSkill(Skill):
    def __init__(self, config: CommonSkillConfig):
        super().__init__(config)
