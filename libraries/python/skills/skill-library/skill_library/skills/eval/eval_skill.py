from assistant_drive import Drive
from skill_library import LanguageModel, Skill, SkillConfig


class EvalSkillConfig(SkillConfig):
    """Configuration for the evaluation skill"""

    language_model: LanguageModel
    drive: Drive


class EvalSkill(Skill):
    config: EvalSkillConfig

    def __init__(self, config: EvalSkillConfig):
        super().__init__(config)
