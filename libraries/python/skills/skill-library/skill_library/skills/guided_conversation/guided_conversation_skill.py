from assistant_drive import Drive
from skill_library import LanguageModel, Skill, SkillConfig

from .guide import ConversationGuide
from .logging import logger

CLASS_NAME = "GuidedConversationSkill"
DESCRIPTION = "Walks the user through a conversation about gathering info for the creation of an artifact."
DEFAULT_MAX_RETRIES = 3
INSTRUCTIONS = "You are an assistant."


class NoDefinitionConfiguredError(Exception):
    pass


class GuidedConversationSkillConfig(SkillConfig):
    """Configuration for the common skill"""

    language_model: LanguageModel
    drive: Drive
    definition: ConversationGuide | None = None


class GuidedConversationSkill(Skill):
    config: GuidedConversationSkillConfig

    def __init__(self, config: GuidedConversationSkillConfig):
        super().__init__(config)

        self.language_model = config.language_model
        self.drive = config.drive

        # Configuring the definition of a conversation here makes this skill
        # instance for this one type (definition) of conversation.
        # Alternatively, you can not supply a definition and have the
        # conversation_init_function take in the definition as a parameter if
        # you wanted to use the same instance for different kinds of
        # conversations.
        if config.definition:
            # If a definition is supplied, we'll use this for every
            # conversation. Save it so we can use it when this skill is run
            # again in the future.
            self.drive.write_model(
                config.definition,
                "GCDefinition.json",
            )
        else:
            # As a convenience, check to see if a definition was already saved
            # previously in this drive.
            try:
                config.definition = self.drive.read_model(ConversationGuide, "GCDefinition.json")
            except FileNotFoundError:
                logger.warning(
                    "No definition supplied or found in the drive. Will expect one as a var in the conversation_init_function"
                )

        self.guide = config.definition
