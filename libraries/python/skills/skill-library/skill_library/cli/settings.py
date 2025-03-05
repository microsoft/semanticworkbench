import json
from pathlib import Path

import yaml
from skill_library.cli.skill_logger import SkillLogger


class Settings:
    """Loads and manages configuration settings from config files."""

    def __init__(self, skills_home_dir: Path, logger: SkillLogger):
        self.config_dir = skills_home_dir / "config"
        # Set data_folder to be at .skills/data rather than under config
        self.data_folder = skills_home_dir / "data"
        self.azure_openai_endpoint = ""
        self.azure_openai_deployment = "gpt-4o"
        self.azure_openai_reasoning_deployment = "o1-mini"
        self.bing_subscription_key = ""
        self.bing_search_url = "https://api.bing.microsoft.com/v7.0/search"
        self.serpapi_api_key = ""
        self.huggingface_token = ""
        self.log_level = "INFO"
        self.logger = logger
        self._load_config()

    def _load_config(self):
        """Load configuration from YAML or JSON files."""
        # Try YAML config first (preferred)
        yaml_config = self.config_dir / "config.yml"
        if yaml_config.exists():
            try:
                with open(yaml_config, "r") as f:
                    config = yaml.safe_load(f)
                    if config:
                        for key, value in config.items():
                            setattr(self, key, value)
                self.logger.info(f"Loaded configuration from {yaml_config}")
                return
            except Exception as e:
                self.logger.warning(f"Failed to load YAML config: {e}")

        # Fall back to JSON config
        json_config = self.config_dir / "config.json"
        if json_config.exists():
            try:
                with open(json_config, "r") as f:
                    config = json.load(f)
                    if config:
                        for key, value in config.items():
                            setattr(self, key, value)
                self.logger.info(f"Loaded configuration from {json_config}")
            except Exception as e:
                self.logger.warning(f"Failed to load JSON config: {e}")
