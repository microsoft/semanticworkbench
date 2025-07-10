# Copyright (c) Microsoft. All rights reserved.

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

from assistant_data_gen.gce.gce_agent import ResourceConstraintMode


class ScenarioConfig(BaseModel):
    description: str = Field(description="The scenario description text")
    gce_conversation_flow: str = Field(description="Conversation flow instructions for this scenario")
    resource_total: int | None = Field(
        default=None, description="Custom resource total for this scenario (if None, uses general config)"
    )


class GeneralConfig(BaseModel):
    assistant_name: str = Field(
        default="Document Assistant 6-13 v1", description="Default name of the assistant to use"
    )
    conversation_title: str = Field(default="GCE Generated Conversation", description="Default title for conversations")
    assistant_details: str = Field(description="Details about the assistant's capabilities")
    gce_context: str = Field(description="Context template for the GCE agent")
    gce_rules: list[str] = Field(description="Rules for the GCE agent")
    resource_total: int = Field(default=50, description="Default total number of resources for conversations")
    resource_constraint_mode: ResourceConstraintMode = Field(
        default=ResourceConstraintMode.EXACT, description="Default resource constraint mode"
    )
    gce_provider: Literal["openai", "anthropic", "azure_openai"] = Field(
        default="azure_openai", description="Default GCE provider to use"
    )


class EvaluationConfig(BaseModel):
    general: GeneralConfig = Field(description="General configuration settings")
    scenarios: list[ScenarioConfig] = Field(description="List of available scenario configurations")

    @classmethod
    def load_from_yaml(cls, config_path: Path | str) -> "EvaluationConfig":
        """Load configuration from a YAML file."""
        config_path = Path(config_path)
        with config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def save_to_yaml(self, config_path: Path | str) -> None:
        """Save configuration to a YAML file."""
        config_path = Path(config_path)
        with config_path.open("w", encoding="utf-8") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False, sort_keys=False)
