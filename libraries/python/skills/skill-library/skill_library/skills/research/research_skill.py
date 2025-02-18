from assistant_drive import Drive
from skill_library import LanguageModel, Skill, SkillConfig


class ResearchSkillConfig(SkillConfig):
    """Configuration for the common skill"""

    language_model: LanguageModel
    drive: Drive


class ResearchSkill(Skill):
    config: ResearchSkillConfig

    def __init__(self, config: ResearchSkillConfig):
        super().__init__(config)
