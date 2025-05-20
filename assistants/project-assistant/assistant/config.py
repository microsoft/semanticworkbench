from semantic_workbench_assistant.assistant_app import (
    BaseModelAssistantConfig,
)

from .configs import (
    AssistantConfigModel,
    CoordinatorConfig,
    KnowledgeTransferConfigModel,
    RequestConfig,
    TeamConfig,
)

assistant_config = BaseModelAssistantConfig(
    AssistantConfigModel,
    additional_templates={
        "knowledge_transfer": KnowledgeTransferConfigModel,
    },
)

__all__ = [
    "AssistantConfigModel",
    "KnowledgeTransferConfigModel",
    "CoordinatorConfig",
    "RequestConfig",
    "TeamConfig",
]
