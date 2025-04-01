from typing import Annotated, Protocol

from pydantic import BaseModel, Field
from semantic_workbench_assistant.assistant_app import ConversationContext


class DocumentEditorConfigModel(BaseModel):
    enabled: Annotated[
        bool,
        Field(title="Enable Document Editor extension"),
    ] = True


class DocumentEditorConfigProvider(Protocol):
    async def __call__(self, ctx: ConversationContext) -> DocumentEditorConfigModel: ...
