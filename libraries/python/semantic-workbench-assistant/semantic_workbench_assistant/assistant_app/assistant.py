from typing import (
    Any,
    Iterable,
    Mapping,
)

import deepmerge
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict

from semantic_workbench_assistant.assistant_app.config import BaseModelAssistantConfig
from semantic_workbench_assistant.assistant_service import create_app

from .content_safety import AlwaysWarnContentSafetyEvaluator, ContentSafety
from .export_import import FileStorageAssistantDataExporter, FileStorageConversationDataExporter
from .protocol import (
    AssistantCapability,
    AssistantConfigProvider,
    AssistantConversationInspectorStateProvider,
    AssistantDataExporter,
    AssistantTemplate,
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
        assistant_service_metadata: dict[str, Any] = {},
        capabilities: set[AssistantCapability] = set(),
        config_provider: AssistantConfigProvider = BaseModelAssistantConfig(EmptyConfigModel).provider,
        data_exporter: AssistantDataExporter = FileStorageAssistantDataExporter(),
        conversation_data_exporter: ConversationDataExporter = FileStorageConversationDataExporter(),
        inspector_state_providers: Mapping[str, AssistantConversationInspectorStateProvider] | None = None,
        content_interceptor: ContentInterceptor | None = ContentSafety(AlwaysWarnContentSafetyEvaluator.factory),
        other_templates: Iterable[AssistantTemplate] = [],
    ) -> None:
        self.assistant_service_id = assistant_service_id
        self.assistant_service_name = assistant_service_name
        self.assistant_service_description = assistant_service_description
        self._assistant_service_metadata = assistant_service_metadata
        self._capabilities = capabilities

        self.config_provider = config_provider
        self.data_exporter = data_exporter
        self.templates = {
            "default": AssistantTemplate(
                id="default",
                name=assistant_service_name,
                description=assistant_service_description,
            ),
        }
        if other_templates:
            for template in other_templates:
                if template.id in self.templates:
                    raise ValueError(f"Template {template.id} already exists")
                self.templates[template.id] = template
        self.conversation_data_exporter = conversation_data_exporter
        self.inspector_state_providers = dict(inspector_state_providers or {})
        self.content_interceptor = content_interceptor

        self.events = Events()

    @property
    def assistant_service_metadata(self) -> dict[str, Any]:
        return deepmerge.always_merger.merge(
            self._assistant_service_metadata,
            {"capabilities": {capability: True for capability in self._capabilities}},
        )

    def add_inspector_state_provider(
        self,
        state_id: str,
        provider: AssistantConversationInspectorStateProvider,
    ) -> None:
        if state_id in self.inspector_state_providers:
            raise ValueError(f"Inspector state provider with id {state_id} already exists")
        self.inspector_state_providers[state_id] = provider

    def add_capability(self, capability: AssistantCapability) -> None:
        self._capabilities.add(capability)

    def fastapi_app(self) -> FastAPI:
        return create_app(
            lambda lifespan: AssistantService(
                assistant_app=self,
                register_lifespan_handler=lifespan.register_handler,
            )
        )
