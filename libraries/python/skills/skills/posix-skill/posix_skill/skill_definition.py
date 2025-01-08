from pathlib import Path
from typing import TYPE_CHECKING, Type

from openai_client.chat_driver import ChatDriverConfig
from skill_library import (
    Skill,
    SkillDefinition,
)

if TYPE_CHECKING:
    from .posix_skill import PosixSkill


NAME = "posix"
CLASS_NAME = "PosixSkill"
DESCRIPTION = "Manages the filesystem using a sand-boxed Posix shell."
DEFAULT_MAX_RETRIES = 3
INSTRUCTIONS = "You are an assistant that has access to a sand-boxed Posix shell."

class PosixSkillDefinition(SkillDefinition):
    def __init__(
        self,
        name: str,
        sandbox_dir: Path,
        mount_dir: str = "/mnt/data",
        description: str | None = None,
        chat_driver_config: ChatDriverConfig | None = None,
        skill_class: Type[Skill] = PosixSkill,
    ) -> None:
        self.name = name
        self.description = description or DESCRIPTION
        self.sandbox_dir = sandbox_dir
        self.mount_dir = mount_dir
        self.chat_driver_config = chat_driver_config
        self.skill_class = skill_class
