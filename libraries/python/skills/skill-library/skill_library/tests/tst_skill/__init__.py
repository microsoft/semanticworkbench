# tst_skill/__init__.py
from skill_library.engine import Skill, SkillConfig


class TstSkillConfig(SkillConfig):
    name: str


class TstSkill(Skill):
    def __init__(self, config: TstSkillConfig):
        super().__init__(config)
        self.call_count = 0  # Add any test state we need
