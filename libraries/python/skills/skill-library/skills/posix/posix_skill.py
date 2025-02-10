from pathlib import Path

from skill_library.engine import Skill, SkillConfig

from .sandbox_shell import SandboxShell


class PosixSkillConfig(SkillConfig):
    """Configuration for the common skill"""

    sandbox_dir: Path
    mount_dir: str = "/mnt/data"


class PosixSkill(Skill):
    shell: SandboxShell

    def __init__(self, config: PosixSkillConfig):
        super().__init__(config)
        self.shell = SandboxShell(config.sandbox_dir, config.mount_dir)
