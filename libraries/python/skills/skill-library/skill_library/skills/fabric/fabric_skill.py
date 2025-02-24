from assistant_drive import Drive
from skill_library import LanguageModel, Skill, SkillConfig


class FabricSkillConfig(SkillConfig):
    language_model: LanguageModel
    drive: Drive


class FabricSkill(Skill):
    config: FabricSkillConfig

    def __init__(self, config: FabricSkillConfig):
        super().__init__(config)
