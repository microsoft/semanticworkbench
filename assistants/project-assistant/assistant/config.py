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

assistant_config = BaseModelAssistantConfig(
    AssistantConfigModel,
    additional_templates={
        "knowledge_transfer": ContextTransferConfigModel,
    },
)

__all__ = [
    "AssistantConfigModel",
    "ContextTransferConfigModel",
    "CoordinatorConfig",
    "RequestConfig",
    "TeamConfig",
]
