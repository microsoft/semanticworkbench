from assistant_drive import Drive
from skill_library import LanguageModel, Skill, SkillConfig


class CommonSkillConfig(SkillConfig):
    """Configuration for the common skill"""

    language_model: LanguageModel
    drive: Drive
    bing_subscription_key: str = ""
    bing_search_url: str = "https://api.bing.microsoft.com/v7.0/search"


class CommonSkill(Skill):
    config: CommonSkillConfig

    def __init__(self, config: CommonSkillConfig):
        super().__init__(config)
