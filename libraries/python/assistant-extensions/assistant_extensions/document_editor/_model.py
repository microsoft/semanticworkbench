from typing import Protocol

from semantic_workbench_assistant.assistant_app import ConversationContext


class DocumentEditorConfigModel(Protocol):
    enabled: bool


class DocumentEditorConfigProvider(Protocol):
    async def __call__(self, ctx: ConversationContext) -> DocumentEditorConfigModel: ...
