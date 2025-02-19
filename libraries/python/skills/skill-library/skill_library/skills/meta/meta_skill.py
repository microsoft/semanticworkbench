from assistant_drive import Drive
from skill_library import LanguageModel, Skill, SkillConfig


class MetaSkillConfig(SkillConfig):
    """Configuration for the skill meta skill"""

    language_model: LanguageModel
    drive: Drive


class MetaSkill(Skill):
    config: MetaSkillConfig

    def __init__(self, config: MetaSkillConfig):
        super().__init__(config)
