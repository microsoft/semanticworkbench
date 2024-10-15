from typing import (
    Mapping,
)

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict

from semantic_workbench_assistant.assistant_service import create_app

from .config import BaseModelAssistantConfig
from .content_safety import AlwaysWarnContentSafetyEvaluator, ContentSafety
from .export_import import FileStorageAssistantDataExporter, FileStorageConversationDataExporter
from .protocol import (
    AssistantConfigProvider,
    AssistantConversationInspectorStateProvider,
    AssistantDataExporter,
    ContentInterceptor,
    ConversationDataExporter,
    Events,
)
from .service import AssistantService


class EmptyConfigModel(BaseModel):
    model_config = ConfigDict(title="This assistant has no configuration")


class AssistantApp:
    def __init__(
        self,
        assistant_service_id: str,
        assistant_service_name: str,
        assistant_service_description: str,
        config_provider: AssistantConfigProvider = BaseModelAssistantConfig(EmptyConfigModel).provider,
        data_exporter: AssistantDataExporter = FileStorageAssistantDataExporter(),
        conversation_data_exporter: ConversationDataExporter = FileStorageConversationDataExporter(),
        inspector_state_providers: Mapping[str, AssistantConversationInspectorStateProvider] | None = None,
        content_interceptor: ContentInterceptor | None = ContentSafety(AlwaysWarnContentSafetyEvaluator.factory),
    ) -> None:
        self.assistant_service_id = assistant_service_id
        self.assistant_service_name = assistant_service_name
        self.assistant_service_description = assistant_service_description

        self.config_provider = config_provider
        self.data_exporter = data_exporter
        self.conversation_data_exporter = conversation_data_exporter
        self.inspector_state_providers = dict(inspector_state_providers or {})
        self.content_interceptor = content_interceptor

        self.events = Events()

    def add_inspector_state_provider(
        self,
        state_id: str,
        provider: AssistantConversationInspectorStateProvider,
    ) -> None:
        if state_id in self.inspector_state_providers:
            raise ValueError(f"Inspector state provider with id {state_id} already exists")
        self.inspector_state_providers[state_id] = provider

    def fastapi_app(self) -> FastAPI:
        return create_app(
            lambda lifespan: AssistantService(
                assistant_app=self,
                register_lifespan_handler=lifespan.register_handler,
            )
        )
