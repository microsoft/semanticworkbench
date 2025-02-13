from typing import Any, Awaitable, Callable

from assistant_drive import Drive
from skill_library import AskUserFn, LanguageModel, RunContext, Skill, SkillConfig

ActionFn = Callable[[RunContext], Awaitable[Any]]
RoutineFn = Callable[[RunContext, AskUserFn], Awaitable[Any]]


class CommonSkillConfig(SkillConfig):
    """Configuration for the common skill"""

    language_model: LanguageModel
    drive: Drive


class CommonSkill(Skill):
    config: CommonSkillConfig

    def __init__(self, config: CommonSkillConfig):
        super().__init__(config)
