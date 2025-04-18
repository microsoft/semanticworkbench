# Export the configuration models from the configs package
from semantic_workbench_assistant.assistant_app import (
    BaseModelAssistantConfig,
)

from .configs import (
    AssistantConfigModel,
    ContextTransferConfigModel,
    CoordinatorConfig,
    RequestConfig,
    TeamConfig,
)

__all__ = [
    "AssistantConfigModel",
    "ContextTransferConfigModel",
    "CoordinatorConfig",
    "RequestConfig",
    "TeamConfig",
]

# Config.
assistant_config = BaseModelAssistantConfig(
    AssistantConfigModel,
    additional_templates={
        "context_transfer": ContextTransferConfigModel,
    },
)
