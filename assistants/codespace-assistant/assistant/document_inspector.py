import io
import logging
from hashlib import md5
from typing import Annotated, Any, Protocol

from pydantic import BaseModel, ValidationError
from semantic_workbench_api_model import workbench_model
from semantic_workbench_assistant.assistant_app import (
    AssistantAppProtocol,
    AssistantConversationInspectorStateDataModel,
    BaseModelAssistantConfig,
    ConversationContext,
)
from semantic_workbench_assistant.config import UISchema, get_ui_schema

from .config import AssistantConfigModel

logger = logging.getLogger(__name__)


class DocumentFileStateModel(BaseModel):
    filename: Annotated[str, UISchema(readonly=True)]
    content: Annotated[str, UISchema(widget="textarea", rows=800, hide_label=True)]


def _get_ui_schema() -> dict[str, Any]:
    schema = get_ui_schema(DocumentFileStateModel)
    schema["ui:options"] = {
        **schema.get("ui:options", {}),
        "collapsible": False,
        "title": "Document Editor",
    }
    return schema


class InspectorController(Protocol):
    async def is_enabled(self, context: ConversationContext) -> bool: ...

    async def get_current_document(self, context: ConversationContext) -> DocumentFileStateModel | None: ...


class EditableDocumentFileStateInspector:
    def __init__(
        self,
        controller: InspectorController,
        display_name: str,
        description: str = "",
    ) -> None:
        self._state_id = md5(
            (type(self).__name__ + "_" + display_name).encode("utf-8"), usedforsecurity=False
        ).hexdigest()
        self._display_name = display_name
        self._description = description
        self._controller = controller

    @property
    def state_id(self) -> str:
        return self._state_id

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def description(self) -> str:
        return self._description

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        if not self._controller.is_enabled(context):
            return AssistantConversationInspectorStateDataModel(
                data={"content": "The Document Editor MCP server is not enabled."}
            )

        document = await self._controller.get_current_document(context)
        if not document:
            return AssistantConversationInspectorStateDataModel(data={"content": "No current document."})

        return AssistantConversationInspectorStateDataModel(
            data=document.model_dump(mode="json"),
            json_schema=document.model_json_schema(),
            ui_schema=_get_ui_schema(),
        )

    async def set(
        self,
        context: ConversationContext,
        data: dict[str, Any],
    ) -> None:
        if not self._controller.is_enabled(context):
            return

        document = await self._controller.get_current_document(context)
        if document is None:
            logger.warning("No file selected for context %s. Cannot set content.", context.id)
            return

        try:
            model = DocumentFileStateModel.model_validate(data)
        except ValidationError:
            logger.exception("invalid data for DocumentFileStateModel")
            return

        await context.write_file(
            filename=document.filename,
            file_content=io.BytesIO(model.content.encode("utf-8")),
            content_type="text/markdown",
        )


class ReadonlyDocumentFileStateInspector:
    def __init__(
        self,
        controller: InspectorController,
        display_name: str,
        description: str = "",
    ) -> None:
        self._state_id = md5(
            (type(self).__name__ + "_" + display_name).encode("utf-8"), usedforsecurity=False
        ).hexdigest()
        self._display_name = display_name
        self._description = description
        self._controller = controller

    @property
    def state_id(self) -> str:
        return self._state_id

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def description(self) -> str:
        return self._description

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        if not self._controller.is_enabled(context):
            return AssistantConversationInspectorStateDataModel(
                data={"content": "The Document Editor MCP server is not enabled."}
            )

        document = await self._controller.get_current_document(context)
        if not document:
            return AssistantConversationInspectorStateDataModel(data={"content": "No current document."})

        return AssistantConversationInspectorStateDataModel(
            data={"content": f"```markdown\n_Filename: {document.filename}_\n\n{document.content}\n```"}
        )


class DocumentInspectors:
    def __init__(
        self,
        app: AssistantAppProtocol,
        config: BaseModelAssistantConfig[AssistantConfigModel],
    ) -> None:
        self._selected_file: dict[str, str] = {}
        self._config = config

        viewer = ReadonlyDocumentFileStateInspector(
            controller=self,
            display_name="Document Viewer",
        )
        app.add_inspector_state_provider(state_id=viewer.state_id, provider=viewer)

        editor = EditableDocumentFileStateInspector(
            controller=self,
            display_name="Document Editor",
        )
        app.add_inspector_state_provider(state_id=editor.state_id, provider=editor)

        @app.events.conversation.file.on_created_including_mine
        @app.events.conversation.file.on_updated_including_mine
        @app.events.conversation.file.on_deleted_including_mine
        async def on_file_change(
            ctx: ConversationContext,
            event: workbench_model.ConversationEvent,
            file: workbench_model.File,
        ) -> None:
            if not file.filename.endswith(".md"):
                return

            self._selected_file[ctx.id] = file.filename
            if event.event == workbench_model.ConversationEventType.file_deleted:
                self._selected_file.pop(ctx.id, None)

            for state_id in (editor.state_id, viewer.state_id):
                await ctx.send_conversation_state_event(
                    workbench_model.AssistantStateEvent(
                        state_id=state_id,
                        event="updated",
                        state=None,
                    )
                )

    async def is_enabled(self, context: ConversationContext) -> bool:
        config = await self._config.get(context.assistant)

        return config.tools.hosted_mcp_servers.filesystem_edit.enabled or any([
            server
            for server in config.tools.personal_mcp_servers
            if server.key == config.tools.hosted_mcp_servers.filesystem_edit.key and server.enabled
        ])

    async def get_current_document(self, context: ConversationContext) -> DocumentFileStateModel | None:
        files_response = await context.list_files()
        markdown_files = [file for file in files_response.files if file.filename.endswith(".md")]
        if not markdown_files:
            self._selected_file.pop(context.id, None)
            return None

        if context.id not in self._selected_file:
            self._selected_file[context.id] = markdown_files[0].filename

        selected_file_name = self._selected_file[context.id]
        selected_file = next((file for file in markdown_files if file.filename == selected_file_name), None)
        if not selected_file:
            return None

        buffer = io.BytesIO()
        async with context.read_file(selected_file.filename) as reader:
            async for chunk in reader:
                buffer.write(chunk)

        file_content = buffer.getvalue().decode("utf-8")

        return DocumentFileStateModel(content=file_content, filename=selected_file.filename)
