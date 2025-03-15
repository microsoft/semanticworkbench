from assistant_drive import Drive
from skill_library import LanguageModel, Skill, SkillConfig


class WebResearchSkillConfig(SkillConfig):
    language_model: LanguageModel
    reasoning_language_model: LanguageModel
    drive: Drive


class WebResearchSkill(Skill):
    config: WebResearchSkillConfig

    def __init__(self, config: WebResearchSkillConfig):
        super().__init__(config)
